from typing import Any, Awaitable, Callable, Sequence, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.tasks.common import TaskInput

type SingleItemFetchFunction[T: TaskInput] = Callable[[T], Awaitable[Any]]
"""
A function that accepts a task input as its only parameter and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this value as input and returns the result.
"""

type BatchFetchFunction[T: TaskInput] = Callable[
    [Sequence[T]], Awaitable[Sequence[Any]]
]
"""
A function that accepts a sequence of task inputs as its only parameter and returns an Awaitable (usually coroutine) which, when awaited, returns a sequence of results (should be one for each input).
"""

type ParamsInput = dict[str, Any] | BaseModel | None


def convert_to_basemodel_instance_of_type[T: BaseModel](
    value: ParamsInput, cls: Type[T]
) -> T:
    """
    Try to convert the input value to an instance of the specified BaseModel subclass, raise appropriate exceptions if that fails.
    """
    if value is None:
        raise ValueError(
            f"Could not construct instance of {cls.__name__} from input as it is None"
        )
    if isinstance(value, dict):
        return cls(**value)  # will raise a ValidationError if the input is invalid
    else:
        if isinstance(value, cls):
            return value
        else:
            raise ValueError(
                f"Could not construct instance of {cls.__name__} from input as it is not an instance of {cls.__name__}"
            )


class DataSourceSingleItemFetchFunctionFactory(ABC):
    """
    A factory for SingleItemFetchFunctions for a specific data source that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    @abstractmethod
    def create(
        self,
        task_type: str,
        task_params: ParamsInput,
    ) -> SingleItemFetchFunction:
        pass


class DataSourceBatchFetchFunctionFactory(ABC):
    """
    A factory for BatchFetchFunctions for a specific data source that can be used by TaskProcessors to do the data fetching without having to know about the exact logic themselves.
    """

    @abstractmethod
    def create(
        self,
        task_type: str,
        task_params: ParamsInput,
    ) -> BatchFetchFunction:
        pass
