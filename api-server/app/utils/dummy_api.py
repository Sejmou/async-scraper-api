from logging import Logger
import random
from asyncio import sleep


class DummyAPIClient:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.logger.info("Dummy API client initialized")

    async def get_dummy_data_from_fake_flaky_endpoint(
        self, id: int, exception_probability: float = 0.1
    ):
        self.logger.info(f"Dummy API client called with id: {id}")
        await sleep(random.uniform(0.1, 0.5))  # Simulate network delay
        if random.random() < exception_probability:
            self.logger.error(
                f"Dummy API returning randomly returning error for id: {id}"
            )
            raise Exception(f"Dummy API error: Random failure for id {id}")
        return {"id": id, "data": "dummy data"}

    async def get_dummy_data_if_id_not_greater_than_threshold(
        self, id: int, threshold: int = 10
    ):
        self.logger.info(f"Dummy API client called with id: {id}")
        await sleep(random.uniform(0.1, 0.5))  # Simulate network delay
        if id > threshold:
            self.logger.error(
                f"Dummy API returning error as ID {id} is greater than threshold {threshold}"
            )
            raise Exception(
                f"Dummy API error: ID {id} is greater than threshold {threshold}"
            )
        return {"id": id, "data": "dummy data"}
