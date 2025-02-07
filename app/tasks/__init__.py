from typing import TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession


from app.db.models import (
    DataSource,
    DataFetchingTask,
    JSONValue,
)
from app.tasks.fetch_functions import (
    create_single_item_fetch_function,
    create_batch_fetch_function,
)

TaskInput = TypeVar("TaskInput", bound=JSONValue)
"""
A type variable for the input to a task. Must be a JSON-serializable value.
"""


async def schedule_new_task[
    T: JSONValue
](
    data_source: DataSource,
    task_type: str,
    params: JSONValue | None,
    s3_bucket: str,
    s3_prefix: str,
    session: AsyncDBSession,
    batch_size: int | None = None,
) -> DataFetchingTask:
    try:
        if batch_size:
            fetch_function = create_batch_fetch_function(data_source, task_type, params)
        else:
            fetch_function = create_single_item_fetch_function(
                data_source, task_type, params
            )
    except Exception as e:
        raise ValueError(
            f"Could not create task for data source {data_source} and task type {task_type}: {e}"
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

    return task
