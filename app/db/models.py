from datetime import datetime
from typing import Literal, get_args
from sqlalchemy import ForeignKey, String, DateTime, Integer, JSON, func, Enum
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Mapped,
    mapped_column,
    relationship,
)

type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[
    str, JSONValue
]


class Base(DeclarativeBase, MappedAsDataclass):
    type_annotation_map = {JSONValue: JSON, list[JSONValue]: JSON}
    """
    This custom type_annotation_map helps us map our custom JSONValue type to the SQLAlchemy JSON type so that we can use our JSONValue type in code, and its gets mapped to the corresponding JSON type in the database.

    See also [StackOverflow discussion](https://stackoverflow.com/a/75678968/13727176) and [docs](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#customizing-the-type-map)
    """


DataSource = Literal["spotify-api"]
"""
The supported data sources for fetching data.
"""

DataFetchingTaskStatus = Literal["pending", "running", "success", "error", "paused"]


class DataFetchingTask(Base):
    __tablename__ = "task"

    """
    This class stores information about an instance of a specific type of data fetching task, most importantly its progress but NOT its results (as they are stored in S3).

    Contrary to the 'runtime tasks' defined in the sibling module `runtime.py`,
    this class should store any information that should be persisted even if the scraper API were to shut down or restart.

    I.e. this data should be sufficient to resume the task at any point in time.
    """

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    # this looks hacky as hell, but is apparently required to make this work in such a way that most sensible type is used in DB automatically AND type hints are correct
    # see also: https://stackoverflow.com/a/76277425/13727176
    status: Mapped[DataFetchingTaskStatus] = mapped_column(
        Enum(
            *get_args(DataFetchingTaskStatus),
            name="data_fetching_task_status",
            create_constraint=True,
            validate_strings=True,
        )
    )

    # this looks hacky as hell, but is apparently required to make this work in such a way that most sensible type is used in DB automatically AND type hints are correct
    # see also: https://stackoverflow.com/a/76277425/13727176
    data_source: Mapped[DataSource] = mapped_column(
        Enum(
            *get_args(DataSource),
            name="data_source",
            create_constraint=True,
            validate_strings=True,
        )
    )
    """
    The source the data is fetched from.

    Example: `spotify-api` for fetching data from the Spotify API.
    """

    task_type: Mapped[str] = mapped_column(String)
    """
    The type of data fetching task. Together with `data_source`, this defines 'what kind of data is fetched from where'.

    Example: `tracks` for fetching track metadata from the Spotify API (assuming `spotify-api` is the `data_source`).
    """

    s3_bucket: Mapped[str] = mapped_column(String)
    """
    The bucket in which output data of the job is stored once all pending inputs are processed or an error occurs that cannot be recovered from and requires user intervention.
    """

    s3_prefix: Mapped[str] = mapped_column(String)
    """
    The S3 prefix in the S3 bucket under which output data of the job is stored once all pending inputs are processed or an error occurs that cannot be recovered from and requires user intervention.
    """

    inputs: Mapped[list["TaskInput"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    """
    The inputs for a task.
    
    Note that only pending inputs, or inputs that resulted in errors or no output are stored here for efficiency reasons - inputs may be in the millions.
    For inputs that are processed successfully, the output is stored in S3 and merely the `success_count` is increased.
    """

    total_input_count: Mapped[int] = mapped_column(Integer)
    """
    The number of inputs that were initially added to the task. Should be passed upon initialization of the task and be equal to the length of the `inputs` list.
    """

    task_meta: Mapped[JSONValue] = mapped_column(JSON, default=None)
    """
    Related metadata for the task. This can be information like the region for which data should be fetched etc.
    """

    success_count: Mapped[int] = mapped_column(default=0)
    """
    The number of inputs that have been processed successfully.
    """

    error_count: Mapped[int] = mapped_column(default=0)
    """
    The number of inputs that have caused an error during processing.
    """

    no_output_count: Mapped[int] = mapped_column(default=0)
    """
    The number of inputs that have been processed successfully, but have not returned any output.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    """
    A non-negative integer representing the number of items that can be processed in parallel (i.e. within a single HTTP request, if fetching data from an API). If 1, the items can only be fetched one by one.
    """

    def __repr__(self) -> str:
        # NOTE: cannot use len(self.inputs) here as it would load all inputs from the database on every call to __repr__ - i.e., every time the object is printed, we would refetch all inputs from the database!
        return f"Task for {self.task_type!r} endpoint (ID: {self.id!r}, metadata: {self.task_meta!r}, S3 prefix: {self.s3_prefix!r}, {self.success_count}/{self.total_input_count} processed successfully)"


TaskItemProcessingStatus = Literal["pending", "success", "error", "no_output"]


class TaskInput(Base):
    __tablename__ = "task_input"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), init=False)
    task: Mapped["DataFetchingTask"] = relationship(back_populates="inputs", init=False)
    data: Mapped[JSONValue] = mapped_column(JSON)

    # this looks hacky as hell, but is apparently required to make this work in such a way that most sensible type is used in DB automatically AND type hints are correct
    # see also: https://stackoverflow.com/a/76277425/13727176
    status: Mapped[TaskItemProcessingStatus] = mapped_column(
        Enum(
            *get_args(TaskItemProcessingStatus),
            name="task_item_processing_status",
            create_constraint=True,
            validate_strings=True,
        )
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime, default=None, nullable=True
    )

    def __repr__(self) -> str:
        return f"Input for task ID {self.task_id!r} ({self.status}): {self.data!r}"


class APIRequestMeta(Base):
    """
    Stores additional metadata about requests made to any API.
    """

    __tablename__ = "api_request_meta"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    url: Mapped[str]
    """
    The complete request URL (including query params)
    """

    status_code: Mapped[int]
    """
    The status code of the response.
    """

    sent_at: Mapped[datetime]
    """
    The time at which the request was sent.
    """

    received_at: Mapped[datetime]
    """
    The time at which the response to the request was received.
    """

    ip: Mapped[str]
    """
    The IP address of the machine that made the request.
    """

    details: Mapped[JSONValue] = mapped_column(JSON, default=None)
    """
    Optional details related to the request or response. May contain things like credentials used, headers etc.
    """


class APIEndpointBlock(Base):
    """
    Stores information about blocked API endpoints for all data sources in the scraper API.
    """

    __tablename__ = "api_endpoint_block"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    data_source: Mapped[str]
    """
    The data source for which the endpoint was blocked.
    """

    endpoint: Mapped[str]
    """
    The endpoint that was blocked.
    """

    blocked_at: Mapped[datetime]
    """
    The time at which the endpoint was blocked.
    """

    blocked_until: Mapped[datetime]
    """
    The time until which the endpoint is blocked.
    """

    details: Mapped[JSONValue] = mapped_column(JSON, default=None)
    """
    Optional details related to the block. May contain things like the IP address that triggered the block, associated API credentials etc.
    """
