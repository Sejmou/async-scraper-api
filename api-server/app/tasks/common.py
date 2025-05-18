from typing import TypedDict
from pydantic import BaseModel

type TaskInput = str | int | BaseModel
"""
Type alias for all values that are 'valid' task inputs.
"""

type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[
    str, JSONValue
]
"""
Any Python value that can be represented as JSON.
"""

type NonNoneJSONValue = str | int | float | bool | list[JSONValue] | dict[
    str, JSONValue
]
"""
Any Python value that can be represented as JSON, excluding None.
"""


class FatalProcessingError(Exception):
    """
    Raised when a fatal error occurs that prevents the task from being processed further at this point in time (e.g. due to API access being blocked)
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TaskProgressMeta(TypedDict):
    """
    A simple dictionary for storing metadata about the progress of a task. Used only to determine if a task update should be reported (not necessarily up-to-date with actual progress)
    """

    successes: int
    failures: int
    inputs_without_output: int
    remaining: int
    current_output_file_size_bytes: int
