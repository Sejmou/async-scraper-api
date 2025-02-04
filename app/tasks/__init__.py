from logging import Logger
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Coroutine, Literal, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db import sessionmanager
from app.db.models import (
    DataSource,
    DataFetchingTask,
    JSONValue,
    TaskInput,
)
from app.tasks.spotify_api import (
    get_single_item_fetch_fn as get_spotify_single_item_fetch_fn,
    get_batch_fetch_fn as get_spotify_batch_fetch_fn,
)

JSONCompat = TypeVar("JSONCompat", bound=JSONValue)
"""
A type variable that represents any JSON-compatible value.
"""

type NonNoneReturnValue = str | int | float | bool | list[JSONValue] | dict
"""
All values that are not None, and convertible to JSON value in all 'cases' except dictionaries*.

*For the sake of simplicity, dicts are not typed strictly (i.e. we use only `dict` - or `dict[Unknown, Unknown]`, to be exact - instead of `dict[str, JSONValue]`).
"""

type ReturnValue = NonNoneReturnValue | None
"""
All values that are convertible to JSON value in all 'cases' except dictionaries*.

*For the sake of simplicity, dicts are not typed strictly (i.e. we use only `dict` - or `dict[Unknown, Unknown]`, to be exact - instead of `dict[str, JSONValue]`).
"""


class ItemDataFetchingResult[JSONCompat](BaseModel):
    input_item: JSONCompat
    """
    The input for which data was fetched.
    """


class DataFetchingSuccess[JSONCompat](ItemDataFetchingResult):
    """
    Returned whenever data fetching for a particular item is successful.
    """

    data: Any
    """
    The result of fetching data for the item. It is guaranteed to be non-None, but deliberately left untyped.
    """


class DataFetchingError[JSONCompat](ItemDataFetchingResult):
    """
    Returned whenever an error occurs while fetching data for a particular item.
    """

    exception: Exception


class DataFetchingNoOutput[JSONCompat](ItemDataFetchingResult):
    """
    Returned whenever data fetching for a particular item did not yield any output.
    """

    pass


type SingleItemFetchFunction[JSONCompat] = Callable[
    [JSONCompat], Coroutine[Any, Any, ItemDataFetchingResult[JSONCompat]]
]
"""
A function that accepts a single JSON-serializable value as input and returns a coroutine which, when awaited, fetches data using this value as input
and returns the result of fetching that item.
"""

type BatchFetchFunction[JSONCompat] = Callable[
    [list[JSONCompat]], Coroutine[Any, Any, list[ItemDataFetchingResult[JSONCompat]]]
]
"""
A function that accepts a list of JSON-serializable values as input and returns a coroutine which, when awaited, fetches data using this list of values as input
and returns a list of equal length containing the results of fetching data for each item.
"""


def create_single_item_fetch_fn[
    JSONCompat
](
    fetch_fn: Callable[[JSONCompat], Awaitable[ReturnValue]],
) -> SingleItemFetchFunction[
    JSONCompat
]:
    async def wrapper_fn(input_item: JSONCompat) -> ItemDataFetchingResult[JSONCompat]:
        try:
            result = await fetch_fn(input_item)
            if result is None:
                return DataFetchingNoOutput[JSONCompat](input_item=input_item)
            return DataFetchingSuccess(input_item=input_item, data=result)
        except Exception as e:
            return DataFetchingError(input_item=input_item, exception=e)

    return wrapper_fn


def create_batch_fetch_fn[
    JSONCompat
](
    fetch_fn: Callable[[list[JSONCompat]], Awaitable[list[ReturnValue]]],
) -> BatchFetchFunction[JSONCompat]:
    async def wrapper_fn(
        input_items: list[JSONCompat],
    ) -> list[ItemDataFetchingResult[JSONCompat]]:
        try:
            fetched_data = await fetch_fn(input_items)
            assert len(fetched_data) == len(
                input_items
            ), f"Result length ({len(fetched_data)}) not matching input length ({len(input_items)})"
            if fetched_data is None:
                return [
                    DataFetchingNoOutput[JSONCompat](input_item=input_item)
                    for input_item in input_items
                ]

            return [
                (
                    DataFetchingSuccess(input_item=input_item, data=data)
                    if data is not None
                    else DataFetchingNoOutput[JSONCompat](input_item=input_item)
                )
                for input_item, data in zip(input_items, fetched_data)
            ]
        except Exception as e:
            return [
                DataFetchingError(input_item=input_item, exception=e)
                for input_item in input_items
            ]

    return wrapper_fn


async def create_task(
    inputs: list[JSONValue],
    data_source: DataSource,
    task_type: str,
    metadata: str,
    s3_bucket: str,
    s3_prefix: str,
    session: AsyncDBSession,
    batch_size: int | None = None,
) -> None:
    task_inputs = [
        TaskInput(data=task_input, status="pending") for task_input in inputs
    ]
    task = DataFetchingTask(
        data_source=data_source,
        task_type=task_type,
        task_meta=metadata,
        status="pending",
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        inputs=task_inputs,
        total_input_count=len(task_inputs),
        batch_size=batch_size or 1,
    )
    session.add(task)
    await session.commit()


class FetchFunctionResolver:
    """
    Finds the appropriate data fetcher for a given task.
    """

    def get_single_item_fetch_fn(
        self, data_source: DataSource, task_type: str
    ) -> SingleItemFetchFunction:
        if data_source == "spotify":
            return get_spotify_single_item_fetch_fn(task_type)
        else:
            raise ValueError(f"Data source '{data_source!r}' is not supported")

    def get_batch_fetch_fn(
        self, data_source: DataSource, task_type: str
    ) -> BatchFetchFunction:
        if data_source == "spotify":
            return get_spotify_batch_fetch_fn(task_type)
        else:
            raise ValueError(f"Data source '{data_source!r}' is not supported")


fetch_fn_resolver = FetchFunctionResolver()


def convert_to_batch_fetch_fn(
    single_item_fetch_fn: SingleItemFetchFunction,
) -> Callable[[list[TaskInput]], Coroutine[Any, Any, list[ItemDataFetchingResult]]]:
    async def fn(input_items: list[TaskInput]) -> list[ItemDataFetchingResult]:
        return [
            await single_item_fetch_fn(input_item.data) for input_item in input_items
        ]

    return fn


class TaskExecutor:
    def __init__(
        self,
        task: DataFetchingTask,
        logger: Logger,
    ):
        self._task = task
        self._logger = logger
        if task.batch_size > 1:
            self._fetch_fn = fetch_fn_resolver.get_batch_fetch_fn(
                task.data_source, task.task_type
            )
        else:
            single_item_fetch_fn = fetch_fn_resolver.get_single_item_fetch_fn(
                task.data_source, task.task_type
            )
            self._fetch_fn = convert_to_batch_fetch_fn(single_item_fetch_fn)

    async def run(
        self,
        logger: Logger,
        retry_failed: bool = False,
        retry_no_output: bool = False,
    ) -> None:
        async with sessionmanager.session() as db_session:
            task = self._task
            if task.status == "running":
                error_msg = f"Task with ID {task.id} is already running"
                logger.error(error_msg)
                raise ValueError(error_msg)

            task.status = "running"

            while task.inputs:
                batch = [
                    task.inputs.pop(0)
                    for _ in range(min(task.batch_size, len(task.inputs)))
                ]
                await self.process_batch(batch)

    async def process_fetch_results(
        self, task: DataFetchingTask, results: list[ItemDataFetchingResult]
    ) -> None:
        pass
