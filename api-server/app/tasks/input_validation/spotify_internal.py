from typing import Annotated, Literal
from pydantic import BaseModel, Field


class RelatedArtistsPayload(BaseModel):
    task_type: Literal["related_artists"] = "related_artists"
    inputs: list[str]


SpotifyInternalApiTaskPayload = Annotated[
    RelatedArtistsPayload, Field(discriminator="task_type")
]


class SpotifyInternalApiTask(BaseModel):
    data_source: Literal["spotify-internal"] = "spotify-internal"
    payload: SpotifyInternalApiTaskPayload
