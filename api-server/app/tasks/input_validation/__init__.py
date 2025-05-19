from typing import Annotated
from pydantic import BaseModel, Field

from app.tasks.input_validation.dummy_api import DummyApiTask
from app.tasks.input_validation.spotify_api import (
    RegionSpecificParams,
    SpotifyApiTask,
    TracksPayload,
)
from app.tasks.input_validation.spotify_internal import SpotifyInternalApiTask

type ValidatedTask = SpotifyApiTask | DummyApiTask | SpotifyInternalApiTask


class ValidatedTaskRoot(BaseModel):
    task: Annotated[
        ValidatedTask,
        Field(discriminator="data_source"),
    ]


def parse_task(data) -> ValidatedTask:
    """
    Parse an arbitrary value into a ValidatedTask instance, raising an exception if that fails.

    Args:
        data: The data to be parsed.

    Returns:
        A ValidatedTask instance.

    Raises:
        ValueError: If the data cannot be parsed into a valid task
    """
    return ValidatedTaskRoot.model_validate({"task": data}).task


test: ValidatedTask = SpotifyApiTask(
    data_source="spotify_api",
    payload=TracksPayload(
        task_type="tracks",
        inputs=["track_id_1", "track_id_2"],
        params=RegionSpecificParams(region="us"),
    ),
)

parse_task(
    {
        "data_source": "spotify_api",
        "payload": {
            "task_type": "tracks",
            "inputs": ["track_id_1", "track_id_2"],
            "params": {"region": "us"},
        },
    }
)
