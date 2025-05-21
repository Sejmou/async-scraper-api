from typing import Annotated, Any
from pydantic import RootModel, Discriminator, Field, Tag, ValidationError

from app.db.models import DataSource
from app.tasks.models.dummy_api import (
    DummyAPITask,
    DummyAPIFlakyTask,
    DummyAPIThrowAboveThresholdTask,
)
from app.tasks.models.spotify_api import (
    SpotifyAPITask,
    SpotifyTracksTask,
    SpotifyAlbumsTask,
    SpotifyArtistsTask,
    SpotifyPlaylistsTask,
    SpotifyArtistAlbumsTask,
)
from app.tasks.models.spotify_internal import (
    SpotifyInternalAPITask,
    SpotifyInternalRelatedArtistsTask,
)

TaskExecutionMeta = SpotifyAPITask | SpotifyInternalAPITask | DummyAPITask


def _get_task_discriminator_value(v: Any) -> str | None:
    if isinstance(v, dict):
        if not "task_type" in v:
            return "task_type_missing"
        if not "data_source" in v:
            return None
        task_type = v["task_type"]
        data_source = v["data_source"]

        return f"{data_source}/{task_type}"

    task_type = getattr(v, "task_type", None)
    if task_type is None:
        return None
    data_source = getattr(v, "data_source", None)
    if data_source is None:
        return None
    return f"{data_source}/{task_type}"


class TaskExecutionMetaModel(RootModel):
    """
    A model storing the important data for execution of any kind of supported task.
    Depending on the `task_type` and `data_source` fields, other specific `inputs` and `params` are defined, as well as a `get_s3_prefix` function.

    The use of `RootModel` allows us to create a model that accepts the task dictionary as input to model_validate, without needing to wrap in another property (e.g. `task`).

    ## Example
    Instead of
    ```python
    TaskExecutionMetaModel.model_validate({"task": {"task_type": "tracks", "data_source": "spotify-api"}})
    ```
    we can do
    ```python
    TaskExecutionMetaModel.model_validate({"task_type": "tracks", "data_source": "spotify-api"})
    ```

    To access the _model_, we still need to use the `root` property.
    ```python
    task = TaskExecutionMetaModel.model_validate({"task_type": "tracks", "data_source": "spotify-api"})
    task.root
    #
    ```

    However, `model_dump_json` will _not_ include the `root` property, but rather only the task dictionary.
    ```python
    task = TaskExecutionMetaModel.model_validate({"task_type": "tracks", "data_source": "spotify-api"})
    task.model_dump_json()
    # {"task_type": "tracks", "data_source": "spotify-api"}
    ```
    """

    root: (
        Annotated[SpotifyTracksTask, Tag("spotify-api/tracks")]
        | Annotated[SpotifyAlbumsTask, Tag("spotify-api/albums")]
        | Annotated[SpotifyArtistsTask, Tag("spotify-api/artists")]
        | Annotated[SpotifyArtistAlbumsTask, Tag("spotify-api/artist-albums")]
        | Annotated[SpotifyPlaylistsTask, Tag("spotify-api/playlists")]
        | Annotated[
            SpotifyInternalRelatedArtistsTask, Tag("spotify-internal/related-artists")
        ]
        | Annotated[DummyAPIFlakyTask, Tag("dummy-api/flaky")]
        | Annotated[
            DummyAPIThrowAboveThresholdTask, Tag("dummy-api/throw-above-threshold")
        ]
    ) = Field(
        discriminator=Discriminator(
            _get_task_discriminator_value,
            custom_error_type="invalid_task_type",
            custom_error_message=f'Could not extract task type. Please provide a valid data source in the "data_source" field and a valid task type for that data source in the "task_type" field.',
        )
    )
    """
    An object representing the task. Most importantly, this contains `inputs` and `params` fields, as well as the `task_type` and `data_source` fields.
    
    The `data_source` and `task_type` fields are used to determine what 'kind of task' we are dealing with and what parameters are therefore relevant (if any).
    """


def get_task_json_schema(data_source: DataSource, task_type: str):
    return TaskExecutionMetaModel.model_validate(
        {"data_source": data_source, "task_type": task_type}
    ).root.model_json_schema()
