from typing import Annotated, Literal
from pydantic import BaseModel, Field

SpotifyInternalRelatedArtistsTaskType = Literal["related-artists"]

SpotifyInternalTaskType = SpotifyInternalRelatedArtistsTaskType

SPOTIFY_INTERNAL_TASK_TYPES: list[SpotifyInternalTaskType] = [
    "related-artists",
]

SpotifyId = Annotated[str, Field(min_length=22, max_length=22)]


class SpotifyInternalTaskBase(BaseModel):
    """
    Base class for all Spotify internal API tasks.
    """

    data_source: Literal["spotify-internal"] = "spotify-internal"
    """
    The data source for the task. This is always "spotify-internal".
    """


class SpotifyInternalRelatedArtistsTask(SpotifyInternalTaskBase):
    """
    Task for fetching related artists from the Spotify internal API.
    """

    task_type: Literal["related-artists"] = "related-artists"

    inputs: list[SpotifyId] = []
    """
    List of Spotify artist IDs to fetch related artists for.
    """

    params: None = None

    def get_s3_prefix(self) -> str:
        return "spotify/internal_apis/related_artists"


SpotifyInternalAPITask = SpotifyInternalRelatedArtistsTask

SpotifyInternalAPITaskParams = None
