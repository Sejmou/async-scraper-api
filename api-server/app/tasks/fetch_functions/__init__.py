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
from app.tasks.fetch_functions.data_sources.spotify_internal import (
    SpotifyInternalAPIBatchFetchFunctionFactory,
    SpotifyInternalAPISingleItemFetchFunctionFactory,
)


class SingleItemFetchFunctionFactory:
    """
    A factory for SingleItemFetchFunctions that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    spotify_api_factory: DataSourceSingleItemFetchFunctionFactory = (
        SpotifyAPISingleItemFetchFunctionFactory()
    )
    spotify_internal_api_factory: DataSourceSingleItemFetchFunctionFactory = (
        SpotifyInternalAPISingleItemFetchFunctionFactory()
    )

    def create(
        self,
        data_source: DataSource,
        task_type: str,
        task_params: ParamsInput,
    ) -> SingleItemFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)
        elif data_source == "spotify-internal":
            return self.spotify_internal_api_factory.create(task_type, task_params)


class BatchFetchFunctionFactory:
    """
    A factory for BatchFetchFunctions that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    spotify_api_factory = SpotifyAPIBatchFetchFunctionFactory()
    spotify_internal_api_factory = SpotifyInternalAPIBatchFetchFunctionFactory()

    def create(
        self,
        data_source: DataSource,
        task_type: str,
        task_params: ParamsInput,
    ) -> BatchFetchFunction:
        if data_source == "spotify-api":
            return self.spotify_api_factory.create(task_type, task_params)
        elif data_source == "spotify-internal":
            return self.spotify_internal_api_factory.create(task_type, task_params)


create_single_item_fetch_function = SingleItemFetchFunctionFactory().create
create_batch_fetch_function = BatchFetchFunctionFactory().create
