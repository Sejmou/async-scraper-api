from typing import Annotated, Any
from pydantic import BaseModel, Discriminator, Field, Tag

from app.tasks.inputs.dummy_api import (
    DummyAPITaskInputs,
    FlakyInputs as DummyFlakyInputs,
    ThrowAboveThresholdInputs as DummyThrowAboveThresholdInputs,
)
from app.tasks.inputs.spotify_api import (
    SpotifyAPITaskInputs,
    TracksInputs as SpotifyTracksInputs,
    AlbumsInputs as SpotifyAlbumsInputs,
    ArtistsInputs as SpotifyArtistsInputs,
    PlaylistsInputs as SpotifyPlaylistsInputs,
    ArtistAlbumsInputs as SpotifyArtistAlbumsInputs,
)
from app.tasks.inputs.spotify_internal import (
    SpotifyInternalAPITaskInputs,
    RelatedArtistsInputs as SpotifyInternalRelatedArtistsInputs,
)


def _get_task_inputs_discriminator_value(v: Any) -> str:
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


TaskInputs = SpotifyAPITaskInputs | SpotifyInternalAPITaskInputs | DummyAPITaskInputs


class _TaskInputsWrapper(BaseModel):
    """
    Model wrapping task inputs (IIUC, there's currently no way to do the Field(discriminator=...) magic without wrapping in a model like this).
    """

    # kinda annoying, but apparently there's no way to achieve what I want without listing every possible task input explicitly
    # TODO: find a more elegant/robust way to do this
    inputs: (
        Annotated[SpotifyTracksInputs, Tag("spotify-api/tracks")]
        | Annotated[SpotifyAlbumsInputs, Tag("spotify-api/albums")]
        | Annotated[SpotifyArtistsInputs, Tag("spotify-api/artists")]
        | Annotated[SpotifyArtistAlbumsInputs, Tag("spotify-api/artist-albums")]
        | Annotated[SpotifyPlaylistsInputs, Tag("spotify-api/playlists")]
        | Annotated[
            SpotifyInternalRelatedArtistsInputs, Tag("spotify-internal/related-artists")
        ]
        | Annotated[DummyFlakyInputs, Tag("dummy-api/flaky")]
        | Annotated[
            DummyThrowAboveThresholdInputs, Tag("dummy-api/throw-above-threshold")
        ]
    ) = Field(discriminator=Discriminator(_get_task_inputs_discriminator_value))
    """
    The relevant parameters for task execution.
    
    The `data_source` and `task_type` fields are used to determine what 'kind of task' we are dealing with and what parameters are therefore relevant (if any).
    """


def parse_task_inputs(data: Any):
    """
    Parse an arbitrary value into a TaskInputs instance, raising an exception if that fails.

    Args:
        data: The data to be parsed.

    Returns:
        A TaskInputs instance.

    Raises:
        ValueError: If the data cannot be parsed into a valid task
    """
    value = _TaskInputsWrapper.model_validate({"inputs": data})
    return value.inputs.inputs
