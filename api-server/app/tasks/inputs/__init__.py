from typing import Annotated, Any, Literal, TypedDict
from pydantic import BaseModel, Discriminator, Field, Tag, ValidationError

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


class InputErrorDetails(TypedDict):
    index: int
    message: str


class InvalidTaskInputsError(Exception):
    """
    Exception raised when task inputs are invalid (i.e. could not be parsed into a valid TaskInputs instance).
    """

    def __init__(
        self,
        message: str,
        code: Literal["invalid-items", "unknown-data-source-or-task-type", "other"],
        invalid_inputs: list[InputErrorDetails] = [],
    ):
        super().__init__(message)
        self.code = code
        self.invalid_inputs = invalid_inputs


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


def parse_task_inputs(inputs: list[Any], data_source: str, task_type: str):
    """
    Parse an arbitrary value into a TaskInputs instance, raising an exception if that fails.

    Args:
        data: The data to be parsed.

    Returns:
        A TaskInputs instance.

    Raises:
        ValueError: If the data cannot be parsed into a valid task
    """
    try:
        value = _TaskInputsWrapper.model_validate(
            {
                "inputs": {
                    "inputs": inputs,
                    "task_type": task_type,
                    "data_source": data_source,
                }
            }
        )
        return (
            value.inputs.inputs
        )  # yeah, this is kinda ugly, but I don't care right now tbh lol
    except ValidationError as e:
        error_details: list[InputErrorDetails] = []
        for error in e.errors():
            if error["type"] == "union_tag_invalid":
                task_type = error["input"].get("task_type")
                data_source = error["input"].get("data_source")
                raise InvalidTaskInputsError(
                    f'Combination of data_source "{data_source}" and task_type "{task_type}" is invalid (or not supported yet)',
                    code="unknown-data-source-or-task-type",
                )

            loc = error["loc"]
            if len(loc) != 4 or loc[0] != "inputs" or loc[2] != "inputs":
                raise InvalidTaskInputsError(
                    f"Invalid task inputs: {error['msg']}",
                    code="other",
                ) from e
            invalid_input_idx = loc[3]
            if not isinstance(invalid_input_idx, int):
                raise InvalidTaskInputsError(
                    f"Invalid task inputs: {error['msg']}",
                    code="other",
                ) from e

            error_details.append(
                {
                    "index": invalid_input_idx,
                    "message": error["msg"],
                }
            )

        if len(error_details) != len(inputs):
            raise InvalidTaskInputsError(
                f"{len(error_details)} inputs were invalid and some other unexpected error(s) occurred, check server logs for details",
                code="invalid-items",
            ) from e

        raise InvalidTaskInputsError(
            f"{len(error_details)} inputs were invalid",
            code="invalid-items",
            invalid_inputs=error_details,
        )
