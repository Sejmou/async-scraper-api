from typing import Annotated, Any
from pydantic import BaseModel, Discriminator, Field, Tag

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

PublicTaskModel = SpotifyAPITask | DummyAPITask | SpotifyInternalAPITask
"""
A model storing all relevant inform
"""


def _get_task_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        if not "task_type" in v:
            raise ValueError("No task_type provided")
        if not "data_source" in v:
            raise ValueError("No data_source provided")
        task_type = v["task_type"]
        data_source = v["data_source"]

        return f"{data_source}/{task_type}"

    task_type = getattr(v, "task_type", None)
    if task_type is None:
        raise ValueError("No task_type property found")
    data_source = getattr(v, "data_source", None)
    if data_source is None:
        raise ValueError("No data_source property found")
    return f"{data_source}/{task_type}"


class TaskWrapper(BaseModel):
    """
    Model wrapping any supported task. This can be used to validate any raw incoming task and its parameters.
    """

    # kinda annoying, but apparently there's no way to achieve what I want without listing every possible task type explicitly
    # TODO: find a more elegant/robust way to do this
    task: (
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
    ) = Field(discriminator=Discriminator(_get_task_discriminator_value))
    """
    An object representing the task. Most importantly, this contains `inputs` and `params` fields, as well as the `task_type` and `data_source` fields.
    
    The `data_source` and `task_type` fields are used to determine what 'kind of task' we are dealing with and what parameters are therefore relevant (if any).
    """


class UnsupportedTaskTypeError(Exception):
    """
    Exception raised when the task type is not supported.
    """

    pass


def get_task_json_schema(data_source: DataSource, task_type: str):
    try:
        return TaskWrapper.model_validate(
            {"task": {"data_source": data_source, "task_type": task_type}}
        ).task.model_json_schema()
    except Exception:
        raise UnsupportedTaskTypeError(
            f'Task type "{task_type}" for data source "{data_source}" is not supported'
        )
