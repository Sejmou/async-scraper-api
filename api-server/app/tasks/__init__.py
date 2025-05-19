import asyncio
from fastapi import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import DataSource, DataFetchingTask, JSONValue
from app.tasks.data_fetching import create_fetch_fn
from app.tasks.metadata import _TaskParamsWrapper
from app.tasks.processing import (
    BatchTaskProcessor,
    SequentialTaskProcessor,
    TaskProcessor,
)
from app.config import app_logger


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


def _create_processor(task_meta: _TaskParamsWrapper) -> TaskProcessor:
    fetch_fn = create_fetch_fn(task_meta.params)


def _create_and_add_processor(task: DataFetchingTask) -> TaskProcessor:
    processor = _create_processor(task)
    app_logger.info(f"Created processor for task ID {task.id}")
    task_processors[task.id] = processor
    app_logger.info(f"Added processor for task ID {task.id} to task processors")
    return processor


def get_task_processor(task: DataFetchingTask) -> TaskProcessor:
    return task_processors.get(task.id) or _create_and_add_processor(task)


async def create_new_task[T: JSONValue](
    data_source: DataSource,
    task_type: str,
    inputs: list[T],
    params: BaseModel | None,
    s3_prefix: str,
    session: AsyncDBSession,
    batch_size: int | None = None,
) -> tuple[DataFetchingTask, TaskProcessor[T]]:
    """
    A utility function for doing all the setup required to create a new data fetching task.

    NOTE: the task is NOT started automatically, you need to call the `run` method on the returned task processor to start processing the inputs.
    """

    if len(inputs) == 0:
        raise ValueError("Cannot create task without inputs!")
    if batch_size is not None and batch_size <= 1:
        raise ValueError("Batch size must be greater than 1!")

    if batch_size:
        batch_fetch_fn = create_batch_fetch_function(data_source, task_type, params)
        if not batch_fetch_fn:
            raise ValueError(
                f"Could not create task: No batched fetch function found for data source {data_source} and task type {task_type}"
            )
    else:
        single_item_fetch_fn = create_single_item_fetch_function(
            data_source, task_type, params
        )
        if not single_item_fetch_fn:
            raise ValueError(
                f"Could not create task: No single-item fetch function found for data source {data_source} and task type {task_type}"
            )

    task = DataFetchingTask(
        data_source=data_source,
        task_type=task_type,
        params=params.model_dump(mode="json") if params else None,
        status="pending",
        s3_prefix=s3_prefix,
        batch_size=batch_size or 1,
    )

    session.add(task)
    await session.commit()

    processor = _create_and_add_processor(task)

    # the task processor maintains its own input queue for the task (data is not stored in the main task DB for performance reasons)
    # so, we need to add the inputs to it separately
    processor.add_inputs(inputs)

    return task, processor
