from typing import Literal, get_args, TypeGuard

from app.tasks.fetch_functions.common import (
    DataSourceSingleItemFetchFunctionFactory,
    DataSourceBatchFetchFunctionFactory,
    SingleItemFetchFunction,
    BatchFetchFunction,
    ParamsInput,
    convert_to_basemodel_instance_of_type,
)
from app.api_clients import dummy_api_client
from app.tasks.input_validation.dummy_api import (
    FlakyParams,
    ThrowAboveThresholdParams,
)

type SequentialTask = Literal["flaky", "throw-above-threshold"]


def is_sequential_task_type(input: str) -> TypeGuard[SequentialTask]:
    return input in get_args(SequentialTask.__value__)


class DummyAPISingleItemFetchFunctionFactory(DataSourceSingleItemFetchFunctionFactory):
    """
    A factory class for creating single-item fetch functions for the Spotify API.
    """

    def create(
        self, task_type: str, task_params: ParamsInput
    ) -> SingleItemFetchFunction:
        if not is_sequential_task_type(task_type):
            raise ValueError(f"Unsupported sequential task type: {task_type}")

        if task_type == "flaky":
            params = convert_to_basemodel_instance_of_type(task_params, FlakyParams)

            async def get_data_as_long_as_below_threshold(input_id: int):
                return await dummy_api_client.get_dummy_data_from_fake_flaky_endpoint(
                    input_id, exception_probability=params.flakiness
                )

            return get_data_as_long_as_below_threshold

        elif task_type == "throw-above-threshold":
            params = convert_to_basemodel_instance_of_type(
                task_params, ThrowAboveThresholdParams
            )

            async def get_data_as_long_as_below_threshold(input_id: int):
                return await dummy_api_client.get_dummy_data_if_id_not_greater_than_threshold(
                    input_id, threshold=params.threshold
                )

            return get_data_as_long_as_below_threshold


class DummyAPIBatchFetchFunctionFactory(DataSourceBatchFetchFunctionFactory):

    def create(self, task_type: str, task_params: ParamsInput) -> BatchFetchFunction:
        raise ValueError(f"Spotify internal API endpoints do not support batching!")
