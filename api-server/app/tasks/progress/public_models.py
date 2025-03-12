from pydantic import BaseModel, ConfigDict
from app.db.models import JSONValue


class TaskProgress(BaseModel):
    """
    This class stores information about the progress of a specific data fetching task instance.

    The underlying data is stored in a dedicated task progress SQLite DB file for each task for efficiency reasons.
    """

    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    success_count: int
    failure_count: int
    inputs_without_output_count: int
    remaining_count: int


class TaskProgressDetails[T: JSONValue](BaseModel):
    """
    This class stores detailed information about the progress of a specific data fetching task instance.

    The underlying data is stored in a dedicated task progress SQLite DB file for each task for efficiency reasons.
    """

    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    successes: list[T]
    failures: list[T]
    inputs_without_output: list[T]
    remaining: list[T]
