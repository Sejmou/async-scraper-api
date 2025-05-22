import asyncio
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import DataFetchingTask
from app.tasks.data_fetching import SingleItemFetchFunctionResult, create_fetch_fn
from app.tasks.models import TaskExecutionMeta, TaskExecutionMetaModel, TaskInputs
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


def _create_processor(db_task: DataFetchingTask) -> TaskProcessor:
    # task DB model stores data_source and task_type in separate fields/columns, but internal logic expects them to be part of params (makes validation logic easier)
    runtime_task = TaskExecutionMetaModel.model_validate(db_task.__dict__).root
    q_mgr = TaskQueueItemManager(task_id=db_task.id, db_dir=TASK_PROGRESS_DB_DIR)
    logger = setup_logger(f"{db_task.id}", file_dir=TASK_LOG_DIR, log_to_console=False)
    fn_res = create_fetch_fn(runtime_task)
    if isinstance(fn_res, SingleItemFetchFunctionResult):
        return SequentialTaskProcessor(
            server_ip=PUBLIC_IP,
            task_id=db_task.id,
            outputs_s3_prefix=runtime_task.get_s3_prefix(),
            outputs_local_storage_dir=TASK_OUTPUT_DIR,
            fetch_fn=fn_res.fn,
            queue_item_manager=q_mgr,
            logger=logger,
        )
    else:
        # fn_res.fn is a function that supports batch processing, fn_res.batch_size stores maximum supported batch size
        return BatchTaskProcessor(
            server_ip=PUBLIC_IP,
            task_id=db_task.id,
            outputs_s3_prefix=runtime_task.get_s3_prefix(),
            outputs_local_storage_dir=TASK_OUTPUT_DIR,
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
    task: TaskExecutionMeta, session: AsyncDBSession
) -> tuple[DataFetchingTask, TaskInputs]:
    """
    Creates a new task in the database and returns it.
    """
    # NOTE: task is stored differently in DB (data_source and task_type are separate columns and NOT included in params object)
    db_task = DataFetchingTask(
        data_source=task.data_source,
        task_type=task.task_type,
        params=(
            task.params.model_dump(mode="json", exclude={"task_type", "data_source"})
            if task.params
            else None
        ),
        # make task paused initially - user still has to start it
        # ('pending' state would cause it to be started and 'done' immediately in the case of a server restart if no inputs were added in the meantime)
        status="paused",
    )

    session.add(db_task)
    await session.commit()

    return db_task, task.inputs
