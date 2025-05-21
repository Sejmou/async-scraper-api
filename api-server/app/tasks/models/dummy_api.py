from typing import Annotated, Literal
from pydantic import BaseModel, Field

DummyFlakyTaskType = Literal["flaky"]
DummyThrowAboveThresholdTaskType = Literal["throw-above-threshold"]

DummyTaskType = DummyFlakyTaskType | DummyThrowAboveThresholdTaskType


class DummyAPITaskBase(BaseModel):
    """
    Base class for all dummy API tasks.
    """

    data_source: Literal["dummy-api"] = "dummy-api"


DummyID = Annotated[int, Field(ge=1)]


class DummyAPIFlakyParams(BaseModel):
    flakiness: float = Field(ge=0, le=1)
    """
    The probability of the dummy API returning an error for a given input. Value should be between 0 and 1.
    """


class DummyAPIFlakyTask(DummyAPITaskBase):
    """
    Task that calls a dummy flaky API endpoint.
    """

    task_type: DummyFlakyTaskType = "flaky"

    inputs: list[DummyID] = []
    """
    List of dummy IDs.
    """

    params: DummyAPIFlakyParams = DummyAPIFlakyParams(flakiness=0.1)

    def get_s3_prefix(self) -> str:
        return f"dummy-api/flaky"


class DummyAPIThrowAboveThresholdParams(BaseModel):
    threshold: int = Field(ge=0, default=10)
    """
    The ID threshold above which the dummy API will return an error for a given input.
    """


class DummyAPIThrowAboveThresholdTask(DummyAPITaskBase):
    """
    Task for testing the dummy API with a throw above threshold response.
    """

    task_type: DummyThrowAboveThresholdTaskType = "throw-above-threshold"

    inputs: list[DummyID] = []
    """
    List of dummy IDs.
    """

    params: DummyAPIThrowAboveThresholdParams = DummyAPIThrowAboveThresholdParams(
        threshold=10
    )

    def get_s3_prefix(self) -> str:
        return f"dummy-api/throw-above-threshold"


DummyAPITask = DummyAPIFlakyTask | DummyAPIThrowAboveThresholdTask


DummyAPITaskParams = DummyAPIFlakyParams | DummyAPIThrowAboveThresholdParams
