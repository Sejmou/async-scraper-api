from app.api_clients import dummy_api_client
from app.tasks.common import (
    SingleItemFetchFunctionResult,
)
from app.tasks.models.dummy_api import (
    DummyAPITask,
)


def create_dummy_api_fetch_fn(task: DummyAPITask):
    if task.task_type == "flaky":

        async def fetch_flaky(
            dummy_id: int,
        ):
            return await dummy_api_client.get_dummy_data_from_fake_flaky_endpoint(
                dummy_id, exception_probability=task.params.flakiness
            )

        return SingleItemFetchFunctionResult(
            fn=fetch_flaky,
        )
    elif task.task_type == "throw-above-threshold":

        async def fetch_throw_above_threshold(
            dummy_id: int,
        ):
            return (
                await dummy_api_client.get_dummy_data_if_id_not_greater_than_threshold(
                    dummy_id, threshold=task.params.threshold
                )
            )

        return SingleItemFetchFunctionResult(
            fn=fetch_throw_above_threshold,
        )
