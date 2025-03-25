from typing import Literal, get_args, TypeGuard

from app.tasks.fetch_functions.common import (
    DataSourceSingleItemFetchFunctionFactory,
    DataSourceBatchFetchFunctionFactory,
    SingleItemFetchFunction,
    BatchFetchFunction,
    ParamsInput,
)
from app.api_clients import spotify_internal_api_client

type SequentialTask = Literal["related_artists"]


def is_sequential_task_type(input: str) -> TypeGuard[SequentialTask]:
    return input in get_args(SequentialTask.__value__)


class SpotifyInternalAPISingleItemFetchFunctionFactory(
    DataSourceSingleItemFetchFunctionFactory
):
    """
    A factory class for creating single-item fetch functions for the Spotify API.
    """

    def create(
        self, task_type: str, task_params: ParamsInput
    ) -> SingleItemFetchFunction:
        if not is_sequential_task_type(task_type):
            raise ValueError(f"Unsupported sequential task type: {task_type}")

        if task_type == "related_artists":
            return spotify_internal_api_client.related_artists


class SpotifyInternalAPIBatchFetchFunctionFactory(DataSourceBatchFetchFunctionFactory):

    def create(self, task_type: str, task_params: ParamsInput) -> BatchFetchFunction:
        raise ValueError(f"Spotify internal API endpoints do not support batching!")
