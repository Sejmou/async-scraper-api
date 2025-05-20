import asyncio
from fastapi import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import DataFetchingTask
from app.tasks.data_fetching import SingleItemFetchFunctionResult, create_fetch_fn
from app.tasks.params import TaskParams, parse_task_params
from app.tasks.processing import (
    BatchTaskProcessor,
    SequentialTaskProcessor,
    TaskProcessor,
)
from app.config import (
    PUBLIC_IP,
    TASK_LOG_DIR,
    TASK_OUTPUT_DIR,
    TASK_PROGRESS_DB_DIR,
    app_logger,
    setup_logger,
)
from app.tasks.queue_item_management import TaskQueueItemManager


task_processors: dict[int, TaskProcessor] = {}


async def run_task(task_processor: TaskProcessor):
    await task_processor.run()
    del task_processors[task_processor.task_id]


def run_in_background(task_processor: TaskProcessor, background_tasks: BackgroundTasks):
    """
    Run the given task processor in the background using the provided FastAPI background tasks manager.
    """
    task_id = task_processor.task_id
    task_processors[task_id] = task_processor

    background_tasks.add_task(run_task, task_processor)


async def correct_stuck_tasks_state_to_pending(db_session: AsyncDBSession):
    """
    Corrects the state of tasks that are 'running' according to the DB but have no associated task processor.

    Should be called on server restart.
    """
    app_logger.info("Checking for stuck tasks...")
    tasks = (
        (
            await db_session.execute(
                select(DataFetchingTask).where(DataFetchingTask.status == "running")
            )
        )
        .scalars()
        .all()
    )
    if not tasks:
        app_logger.info("No stuck tasks found")
        return

    for task in tasks:
        if task.id not in task_processors:
            task.status = "pending"
            await db_session.commit()
            app_logger.info(
                f"Corrected stuck task with ID {task.id} to 'pending' state"
            )


async def resume_pending_tasks(db_session: AsyncDBSession):
    """
    Resumes all tasks that are currently in pending state and have no associated task processor.

    Should be called on server restart (after correcting the state of stuck tasks).
    """
    app_logger.info("Checking for pending tasks...")
    tasks = (
        (
            await db_session.execute(
                select(DataFetchingTask).where(DataFetchingTask.status == "pending")
            )
        )
        .scalars()
        .all()
    )
    if not tasks:
        app_logger.info("No pending tasks")
        return

    for task in tasks:
        processor = task_processors.get(task.id) or _create_and_add_processor(task)
        task_processors[task.id] = processor
        app_logger.info(f"Resuming task with ID {task.id}...")
        asyncio.create_task(run_task(processor))


def _create_processor(task: DataFetchingTask) -> TaskProcessor:
    # parse the task parameters; need to do some stupid transforms to make it work
    # TODO: refactor this mess lol
    params = parse_task_params(
        {
            **(task.params or {}),
            "data_source": task.data_source,
            "task_type": task.task_type,
        }
    )
    q_mgr = TaskQueueItemManager(task_id=task.id, db_dir=TASK_PROGRESS_DB_DIR)
    logger = setup_logger(f"{task.id}", file_dir=TASK_LOG_DIR, log_to_console=False)
    fn_res = create_fetch_fn(params)
    if isinstance(fn_res, SingleItemFetchFunctionResult):
        return SequentialTaskProcessor(
            server_ip=PUBLIC_IP,
            task_id=task.id,
            outputs_dir=TASK_OUTPUT_DIR,
            fetch_fn=fn_res.fn,
            queue_item_manager=q_mgr,
            logger=logger,
        )
    else:
        # fn_res.fn is a function that supports batch processing, fn_res.batch_size stores maximum supported batch size
        return BatchTaskProcessor(
            server_ip=PUBLIC_IP,
            task_id=task.id,
            outputs_dir=TASK_OUTPUT_DIR,
            fetch_fn=fn_res.fn,
            queue_item_manager=q_mgr,
            logger=logger,
            batch_size=fn_res.batch_size,
        )


def _create_and_add_processor(task: DataFetchingTask) -> TaskProcessor:
    processor = _create_processor(task)
    app_logger.info(f"Created processor for task ID {task.id}")
    task_processors[task.id] = processor
    app_logger.info(f"Added processor for task ID {task.id} to task processors")
    return processor


def get_task_processor(task: DataFetchingTask) -> TaskProcessor:
    return task_processors.get(task.id) or _create_and_add_processor(task)


async def create_new_task(
    params: TaskParams, s3_prefix: str, session: AsyncDBSession
) -> DataFetchingTask:
    """
    Creates a new task in the database and returns it.
    """
    # NOTE: task is stored differently in DB (data_source and task_type are separate columns and NOT included in params object)
    task = DataFetchingTask(
        data_source=params.data_source,
        task_type=params.task_type,
        params=params.model_dump(mode="json", exclude={"task_type", "data_source"}),
        status="pending",
        s3_prefix=s3_prefix,
    )

    session.add(task)
    await session.commit()

    return task
