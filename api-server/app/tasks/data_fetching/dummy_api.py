from app.api_clients import dummy_api_client
from app.tasks.data_fetching import (
    SingleItemFetchFunctionResult,
)
from app.tasks.params.dummy_api import DummyAPITaskParams


def create_dummy_api_fetch_fn(
    params: DummyAPITaskParams,
):
    if params.task_type == "flaky":

        async def fetch_flaky(
            dummy_id: int,
        ):
            return await dummy_api_client.get_dummy_data_from_fake_flaky_endpoint(
                dummy_id, exception_probability=params.flakiness
            )

        return SingleItemFetchFunctionResult(
            fn=fetch_flaky,
        )
    elif params.task_type == "throw-above-threshold":

        async def fetch_throw_above_threshold(
            dummy_id: int,
        ):
            return (
                await dummy_api_client.get_dummy_data_if_id_not_greater_than_threshold(
                    dummy_id, threshold=params.threshold
                )
            )

        return SingleItemFetchFunctionResult(
            fn=fetch_throw_above_threshold,
        )
