from dataclasses import dataclass
from app.tasks.common import BatchFetchFunction, SingleItemFetchFunction, TaskInput
from app.tasks.params import TaskParams
from app.tasks.data_fetching.dummy_api import create_dummy_api_fetch_fn
from app.tasks.data_fetching.spotify_api import create_spotify_api_fetch_fn
from app.tasks.data_fetching.spotify_internal import (
    create_spotify_internal_api_fetch_fn,
)


@dataclass
class SingleItemFetchFunctionResult[T: TaskInput]:
    """
    A wrapper for a single item fetch function. Required because in Python, we cannot determine the exact type of a function (most importantly, the type of it's arguments) at runtime.
    """

    fn: SingleItemFetchFunction[T]


@dataclass
class BatchFetchFunctionResult[T: TaskInput]:
    """
    A wrapper for a batch item fetch function. Required because in Python, we cannot determine the exact type of a function (most importantly, the type of it's arguments) at runtime.
    """

    fn: BatchFetchFunction[T]
    batch_size: int


def create_fetch_fn(
    params: TaskParams,
) -> SingleItemFetchFunctionResult | BatchFetchFunctionResult:
    if params.data_source == "spotify-api":
        return create_spotify_api_fetch_fn(params)
    elif params.data_source == "spotify-internal":
        return create_spotify_internal_api_fetch_fn(params)
    elif params.data_source == "dummy-api":
        return create_dummy_api_fetch_fn(params)
