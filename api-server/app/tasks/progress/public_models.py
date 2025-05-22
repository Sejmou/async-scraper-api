from pydantic import BaseModel, ConfigDict


class TaskProgressModel(BaseModel):
    """
    This class stores information about the progress of a specific data fetching task instance.

    The underlying data is stored in a dedicated task progress SQLite DB file for each task for efficiency reasons.
    """

    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    success_count: int
    """
    The number of items that have been successfully processed.
    """

    failure_count: int
    """
    The number of items that have failed to process, i.e. produced a non-fatal error during processing.
    """

    inputs_without_output_count: int
    """
    The number of items that have been processed but produced no output.
    """

    remaining_count: int
    """
    The number of items that are left to process.
    """
