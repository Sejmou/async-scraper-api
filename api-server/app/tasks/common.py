from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Sequence, TypedDict


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

type SingleItemFetchFunction[T] = Callable[[T], Awaitable[Any]]
"""
A function that accepts a task input as its only parameter and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this value as input and returns the result.
"""

type BatchFetchFunction[T] = Callable[[Sequence[T]], Awaitable[Sequence[Any]]]
"""
A function that accepts a sequence of task inputs as its only parameter and returns an Awaitable (usually coroutine) which, when awaited, returns a sequence of results (should be one for each input).
"""


@dataclass
class SingleItemFetchFunctionResult[T]:
    """
    A wrapper for a single item fetch function. Required because in Python, we cannot determine the exact type of a function (most importantly, the type of it's arguments) at runtime.
    """

    fn: SingleItemFetchFunction[T]


@dataclass
class BatchFetchFunctionResult[T]:
    """
    A wrapper for a batch item fetch function. Required because in Python, we cannot determine the exact type of a function (most importantly, the type of it's arguments) at runtime.
    """

    fn: BatchFetchFunction[T]
    batch_size: int


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
