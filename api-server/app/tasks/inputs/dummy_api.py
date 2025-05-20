from typing import Literal
from pydantic import BaseModel


class DummyInputsBase(BaseModel):
    """
    Base class for all dummy API task inputs.
    """

    data_source: Literal["dummy-api"] = "dummy-api"


class FlakyInputs(DummyInputsBase):
    task_type: Literal["flaky"] = "flaky"
    inputs: list[int]


class ThrowAboveThresholdInputs(DummyInputsBase):
    task_type: Literal["throw-above-threshold"] = "throw-above-threshold"
    inputs: list[int]


DummyAPITaskInputs = FlakyInputs | ThrowAboveThresholdInputs
