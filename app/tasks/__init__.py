from fastapi import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import DataSource, DataFetchingTask, JSONValue
from app.tasks.fetch_functions import (
    create_single_item_fetch_function,
    create_batch_fetch_function,
    SingleItemFetchFunction,
    BatchFetchFunction,
)
from app.tasks.processing import (
    BatchTaskProcessor,
    SequentialTaskProcessor,
    TaskProcessor,
)


task_processors: dict[int, TaskProcessor] = {}


def run_in_background(task_processor: TaskProcessor, background_tasks: BackgroundTasks):
    """
    Run the given task processor in the background using the provided FastAPI background tasks manager.
    """
    task_id = task_processor.task_id
    task_processors[task_id] = task_processor

    async def run_task():
        await task_processor.run()
        del task_processors[task_id]

    background_tasks.add_task(run_task)


def pause_task(task_id: int):
    """
    Pause a task processor with the given ID.
    """
    task_processor = task_processors.get(task_id)
    if task_processor:
        task_processor.pause()
    else:
        raise ValueError(f"No task processor found with ID {task_id}")


def resume_task(task_id: int, background_tasks: BackgroundTasks):
    """
    Resume a task processor with the given ID.
    """
    task_processor = task_processors.get(task_id)
    if task_processor:
        run_in_background(task_processor, background_tasks)
    else:
        raise ValueError(f"No task processor found with ID {task_id}")


async def create_new_task[T: JSONValue](
    data_source: DataSource,
    task_type: str,
    inputs: list[T],
    params: BaseModel | None,
    s3_bucket: str,
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

    # Every task (or, more specifically, its processor) requires a fetch function for the passed data source and task type (accepting batches of data if batch_size is > 1, or single items otherwise)
    # unfortunately, we cannot check the type of function we get back at runtime, so this ugly hack is used instead
    single_item_fetch_fn: SingleItemFetchFunction[T] | None = None
    batch_fetch_fn: BatchFetchFunction[T] | None = None
    try:
        if batch_size:
            batch_fetch_fn = create_batch_fetch_function(data_source, task_type, params)
        else:
            single_item_fetch_fn = create_single_item_fetch_function(
                data_source, task_type, params
            )
    except Exception as e:
        raise ValueError(
            f"Could not create task for data source {data_source} and task type {task_type} due to error finding suitable fetch function: {e}"
        )

    task = DataFetchingTask(
        data_source=data_source,
        task_type=task_type,
        params=params.model_dump(mode="json") if params else None,
        status="pending",
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        batch_size=batch_size or 1,
    )

    session.add(task)
    await session.commit()

    if batch_size:
        if not batch_fetch_fn:
            # NOTE: this should be impossible, if it happens it's definitely a bug
            raise ValueError(
                f"Could not create task processor for task with ID {task.id} as no batched fetch function was found"
            )
        processor = BatchTaskProcessor[T](
            task_id=task.id,
            fetch_fn=batch_fetch_fn,
            batch_size=batch_size,
        )
    else:
        if not single_item_fetch_fn:
            # NOTE: this should be impossible, if it happens it's definitely a bug
            raise ValueError(
                f"Could not create task processor for task with ID {task.id} as no single-item fetch function was found"
            )
        processor = SequentialTaskProcessor[T](
            task_id=task.id,
            fetch_fn=single_item_fetch_fn,
        )

    # the task processor maintains its own input queue for the task (not stored in the main task DB for performance reasons), so we need to add the inputs to it separately
    processor.add_inputs(inputs)

    return task, processor
