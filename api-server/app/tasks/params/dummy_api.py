from typing import Literal
from pydantic import BaseModel, Field


class DummyParamsBase(BaseModel):
    """
    Base class for all dummy API task parameters.
    """

    data_source: Literal["dummy-api"] = "dummy-api"


class FlakyParams(DummyParamsBase):
    task_type: Literal["flaky"] = "flaky"

    flakiness: float = Field(ge=0, le=1)
    """
    The probability of the dummy API returning an error for a given input. Value should be between 0 and 1.
    """


class ThrowAboveThresholdParams(DummyParamsBase):
    task_type: Literal["throw-above-threshold"] = "throw-above-threshold"

    threshold: int = Field(ge=0, default=10)
    """
    The ID threshold above which the dummy API will return an error for a given input.
    """


DummyAPITaskParams = FlakyParams | ThrowAboveThresholdParams
