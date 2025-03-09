from abc import ABC, abstractmethod

from app.tasks.fetch_functions.common import (
    DataSourceSingleItemFetchFunctionFactory,
    SingleItemFetchFunction,
    BatchFetchFunction,
    ParamsInput,
)
from app.db.models import DataSource
from app.tasks.fetch_functions.data_sources.spotify_api import (
    SpotifyAPISingleItemFetchFunctionFactory,
    SpotifyAPIBatchFetchFunctionFactory,
)


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
        task_params: ParamsInput,
    ) -> SingleItemFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)


class BatchFetchFunctionFactory:
    """
    A factory for BatchFetchFunctions that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    spotify_api_factory = SpotifyAPIBatchFetchFunctionFactory()

    def create(
        self,
        data_source: DataSource,
        task_type: str,
        task_params: ParamsInput,
    ) -> BatchFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)


create_single_item_fetch_function = SingleItemFetchFunctionFactory().create
create_batch_fetch_function = BatchFetchFunctionFactory().create
