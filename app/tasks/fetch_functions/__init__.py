from typing import Any, Awaitable, Callable
from abc import ABC, abstractmethod
from app.db.models import JSONValue, DataSource
from app.tasks.fetch_functions.spotify_api import (
    SpotifyAPISingleItemFetchFunctionFactory,
    SpotifyAPIBatchFetchFunctionFactory,
)

type SingleItemFetchFunction[T: JSONValue] = Callable[[T], Awaitable[Any]]
"""
A function that accepts a single value of a specific JSON-serializable type as input and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this value as input and returns the result.
"""

type BatchFetchFunction[T: JSONValue] = Callable[[list[T]], Awaitable[list[Any]]]
"""
A function that accepts a list of values of a specific JSON-serializable type as input and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this list of values as input and returns the results in a list of values.
"""


class DataSourceSingleItemFetchFunctionFactory(ABC):
    """
    A factory for SingleItemFetchFunctions for a specific data source that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    @abstractmethod
    def create(
        self,
        task_type: str,
        task_params: dict[str, Any] | None,
    ) -> SingleItemFetchFunction:
        pass


class SingleItemFetchFunctionFactory:
    """
    A factory for SingleItemFetchFunctions that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    spotify_api_factory: DataSourceSingleItemFetchFunctionFactory = (
        SpotifyAPISingleItemFetchFunctionFactory()
    )

    def create(
        self,
        data_source: DataSource,
        task_type: str,
        task_params: dict[str, Any] | None,
    ) -> SingleItemFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)


class DataSourceBatchFetchFunctionFactory(ABC):
    """
    A factory for BatchFetchFunctions for a specific data source that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    @abstractmethod
    def create(
        self,
        task_type: str,
        task_params: dict[str, Any] | None,
    ) -> BatchFetchFunction:
        pass


class BatchFetchFunctionFactory:
    """
    A factory for BatchFetchFunctions that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    spotify_api_factory = SpotifyAPIBatchFetchFunctionFactory()

    def create(
        self,
        data_source: DataSource,
        task_type: str,
        task_params: dict[str, Any] | None,
    ) -> BatchFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)


create_single_item_fetch_function = SingleItemFetchFunctionFactory().create
create_batch_fetch_function = BatchFetchFunctionFactory().create
