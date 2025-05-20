from typing import Annotated, Any
from pydantic import BaseModel, Discriminator, Field, Tag

from app.tasks.params.dummy_api import (
    DummyAPITaskParams,
    FlakyParams as DummyFlakyParams,
    ThrowAboveThresholdParams as DummyThrowAboveThresholdParams,
)
from app.tasks.params.spotify_api import (
    SpotifyAPITaskParams,
    TracksParams as SpotifyTracksParams,
    AlbumsParams as SpotifyAlbumsParams,
    ArtistsParams as SpotifyArtistsParams,
    PlaylistsParams as SpotifyPlaylistsParams,
    ArtistAlbumsParams as SpotifyArtistAlbumsParams,
)
from app.tasks.params.spotify_internal import (
    SpotifyInternalAPITaskParams,
    RelatedArtistsParams as SpotifyInternalRelatedArtistsParams,
)

TaskParams = SpotifyAPITaskParams | SpotifyInternalAPITaskParams | DummyAPITaskParams


def _get_task_params_discriminator_value(v: Any) -> str:
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


class _TaskParamsWrapper(BaseModel):
    """
    Model wrapping task parameters (IIUC, there's currently no way to do the Field(discriminator=...) magic without wrapping in a model like this).
    """

    # kinda annoying, but apparently there's no way to achieve what I want without listing every possible task type explicitly
    # TODO: find a more elegant/robust way to do this
    params: (
        Annotated[SpotifyTracksParams, Tag("spotify-api/tracks")]
        | Annotated[SpotifyAlbumsParams, Tag("spotify-api/albums")]
        | Annotated[SpotifyArtistsParams, Tag("spotify-api/artists")]
        | Annotated[SpotifyArtistAlbumsParams, Tag("spotify-api/artist-albums")]
        | Annotated[SpotifyPlaylistsParams, Tag("spotify-api/playlists")]
        | Annotated[
            SpotifyInternalRelatedArtistsParams, Tag("spotify-internal/related-artists")
        ]
        | Annotated[DummyFlakyParams, Tag("dummy-api/flaky")]
        | Annotated[
            DummyThrowAboveThresholdParams, Tag("dummy-api/throw-above-threshold")
        ]
    ) = Field(discriminator=Discriminator(_get_task_params_discriminator_value))
    """
    The relevant parameters for task execution.
    
    The `data_source` and `task_type` fields are used to determine what 'kind of task' we are dealing with and what parameters are therefore relevant (if any).
    """


def parse_task_params(data: Any) -> TaskParams:
    """
    Parse an arbitrary value into a TaskParams instance, raising an exception if that fails.

    Args:
        data: The data to be parsed.

    Returns:
        A TaskParams instance.

    Raises:
        ValueError: If the data cannot be parsed into a valid task
    """
    value = _TaskParamsWrapper.model_validate({"params": data})
    return value.params
