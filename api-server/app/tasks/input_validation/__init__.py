from typing import Annotated
from pydantic import Field

from app.tasks.input_validation.dummy_api import DummyApiTask
from app.tasks.input_validation.spotify_api import SpotifyApiTask
from app.tasks.input_validation.spotify_internal import SpotifyInternalApiTask

ValidatedTask = Annotated[
    SpotifyApiTask | DummyApiTask | SpotifyInternalApiTask,
    Field(discriminator="data_source"),
]
