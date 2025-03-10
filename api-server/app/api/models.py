from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.db.models import JSONValue, DataSource, DataFetchingTaskStatus


class DataFetchingTask(BaseModel):
    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    """
    This class stores information about an instance of a specific type of data fetching task, most importantly its progress but NOT its results (as they are stored in S3).

    Contrary to the 'runtime tasks' defined in the sibling module `runtime.py`,
    this class should store any information that should be persisted even if the scraper API were to shut down or restart.

    I.e. this data should be sufficient to resume the task at any point in time.
    """

    id: int

    status: DataFetchingTaskStatus

    data_source: DataSource
    """
    The source the data is fetched from.

    Example: `spotify-api` for fetching data from the Spotify API.
    """

    task_type: str
    """
    The type of data fetching task. Together with `data_source`, this defines 'what kind of data is fetched from where'.

    Example: `tracks` for fetching track metadata from the Spotify API (assuming `spotify-api` is the `data_source`).
    """

    s3_bucket: str
    """
    The bucket in which output data of the job is stored once all pending inputs are processed or an error occurs that cannot be recovered from and requires user intervention.
    """

    s3_prefix: str
    """
    The S3 prefix in the S3 bucket under which output data of the job is stored once all pending inputs are processed or an error occurs that cannot be recovered from and requires user intervention.
    """

    file_uploads: list["S3FileUpload"]
    """
    The files that have been uploaded to S3 as part of this task.
    """

    lines_written_to_current_output_file: int
    """
    The number of lines written to the current output file.
    """

    success_count: int
    """
    The number of items for which data has been fetched successfully so far.
    """

    params: dict[str, JSONValue] | None
    """
    Optional additional parameters for the task.
    """

    created_at: datetime
    updated_at: datetime

    batch_size: int


class S3FileUpload(BaseModel):
    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    id: int
    task_id: int

    s3_key: str

    s3_bucket: str

    s3_endpoint_url: str

    size_bytes: int

    output_count: int
    """
    The number of input items for which a non-None output was written to this file (should be equal to the row count).
    """

    task: DataFetchingTask
    """
    The task this file was uploaded as part of.
    """

    uploaded_at: datetime
