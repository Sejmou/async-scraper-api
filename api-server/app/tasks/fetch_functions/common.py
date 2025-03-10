from app.db.models import JSONValue
from typing import Any, Awaitable, Callable, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel

type SingleItemFetchFunction[T: JSONValue] = Callable[[T], Awaitable[Any]]
"""
A function that accepts a single value of a specific JSON-serializable type as input and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this value as input and returns the result.
"""

type BatchFetchFunction[T: JSONValue] = Callable[[list[T]], Awaitable[list[Any]]]
"""
A function that accepts a list of values of a specific JSON-serializable type as input and returns an Awaitable (usually coroutine) which, when awaited, fetches data using this list of values as input and returns the results in a list of values.
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
