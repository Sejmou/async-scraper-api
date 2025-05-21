from app.tasks.common import BatchFetchFunctionResult, SingleItemFetchFunctionResult
from app.tasks.models import TaskExecutionMeta
from app.tasks.data_fetching.dummy_api import create_dummy_api_fetch_fn
from app.tasks.data_fetching.spotify_api import create_spotify_api_fetch_fn
from app.tasks.data_fetching.spotify_internal import (
    create_spotify_internal_api_fetch_fn,
)


def create_fetch_fn(
    task: TaskExecutionMeta,
) -> SingleItemFetchFunctionResult | BatchFetchFunctionResult:
    if task.data_source == "spotify-api":
        return create_spotify_api_fetch_fn(task)
    elif task.data_source == "spotify-internal":
        return create_spotify_internal_api_fetch_fn(task)
    elif task.data_source == "dummy-api":
        return create_dummy_api_fetch_fn(task)
