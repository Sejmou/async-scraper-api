from app.tasks.common import BatchFetchFunctionResult, SingleItemFetchFunctionResult
from app.tasks.params import TaskParams
from app.tasks.data_fetching.dummy_api import create_dummy_api_fetch_fn
from app.tasks.data_fetching.spotify_api import create_spotify_api_fetch_fn
from app.tasks.data_fetching.spotify_internal import (
    create_spotify_internal_api_fetch_fn,
)


def create_fetch_fn(
    params: TaskParams,
) -> SingleItemFetchFunctionResult | BatchFetchFunctionResult:
    if params.data_source == "spotify-api":
        return create_spotify_api_fetch_fn(params)
    elif params.data_source == "spotify-internal":
        return create_spotify_internal_api_fetch_fn(params)
    elif params.data_source == "dummy-api":
        return create_dummy_api_fetch_fn(params)
