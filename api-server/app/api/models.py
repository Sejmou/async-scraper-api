from pydantic import BaseModel, ConfigDict, RootModel
from datetime import datetime

from app.db.models import JSONValue, DataSource, DataFetchingTaskStatus
from app.tasks.progress.public_models import TaskProgressModel


class DataFetchingTaskModel(BaseModel):
    model_config = ConfigDict(
        # from_attributes allows creation of instances of this class from the ORM model (which shares the same properties/types as attributes)
        from_attributes=True
    )

    """
    This class stores information about an instance of a specific type of data fetching task information that should be persisted even if the scraper API were to shut down or restart.

    Does NOT include information about the _progress_ of the task. This data is stored in a dedicated task progress SQLite DB file for each task for efficiency reasons.
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

    file_uploads: list["S3FileUploadModel"]
    """
    The files that have been uploaded to S3 as part of this task.
    """

    params: dict[str, JSONValue] | None
    """
    Optional additional parameters for the task.
    """

    created_at: datetime
    updated_at: datetime


class S3FileUploadModel(BaseModel):
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

    uploaded_at: datetime
