from pydantic import BaseModel, Field


class FlakyParams(BaseModel):
    """
    Parameters for the dummy API that simulates flakiness.
    """

    flakiness: float = Field(ge=0, le=1)
    """
    The probability of the dummy API returning an error for a given input. Value should be between 0 and 1.
    """


class FlakyPayload(BaseModel):
    inputs: list[int]
    """
    The list of IDs to be processed by the dummy API.
    """

    params: FlakyParams


class ThrowAboveThresholdParams(BaseModel):
    """
    Parameters for the dummy API that throws an error if the ID is above a certain threshold.
    """

    threshold: int = Field(ge=0, default=10)
    """
    The ID threshold above which the dummy API will return an error for a given input.
    """


class ThrowAboveThresholdPayload(BaseModel):
    inputs: list[int]
    """
    The list of IDs to be processed by the dummy API.
    """

    params: ThrowAboveThresholdParams
