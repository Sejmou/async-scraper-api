from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Literal

SpotifyTracksTaskType = Literal["tracks"]
SpotifyArtistsTaskType = Literal["artists"]
SpotifyAlbumsTaskType = Literal["albums"]
SpotifyArtistAlbumsTaskType = Literal["artist-albums"]
SpotifyISRCTrackSearchTaskType = Literal["isrc-track-search"]
SpotifyPlaylistsTaskType = Literal["playlists"]

SpotifyAPITaskType = (
    SpotifyTracksTaskType
    | SpotifyArtistsTaskType
    | SpotifyAlbumsTaskType
    | SpotifyArtistAlbumsTaskType
    | SpotifyISRCTrackSearchTaskType
    | SpotifyPlaylistsTaskType
)

SPOTIFY_API_TASK_TYPES: list[SpotifyAPITaskType] = [
    "tracks",
    "artists",
    "albums",
    "artist-albums",
    "isrc-track-search",
    "playlists",
]


class SpotifyTaskBase(BaseModel):
    """
    Base class for all Spotify API tasks.
    """

    data_source: Literal["spotify-api"] = "spotify-api"


DataFetchingRegion = Literal["de", "us"]

SpotifyId = Annotated[str, Field(min_length=22, max_length=22)]


class SpotifyTracksParams(BaseModel):
    region: DataFetchingRegion


class SpotifyTracksTask(SpotifyTaskBase):
    task_type: SpotifyTracksTaskType = "tracks"
    inputs: list[SpotifyId] = []
    params: SpotifyTracksParams = SpotifyTracksParams(region="de")

    def get_s3_prefix(self) -> str:
        return f"spotify/tracks_{self.params.region}"


class SpotifyArtistsTask(SpotifyTaskBase):
    task_type: SpotifyArtistsTaskType = "artists"
    inputs: list[SpotifyId] = []
    params: None = None

    def get_s3_prefix(self) -> str:
        return "spotify/artists"


class SpotifyAlbumsParams(BaseModel):
    region: DataFetchingRegion


class SpotifyAlbumsTask(SpotifyTaskBase):
    task_type: SpotifyAlbumsTaskType = "albums"
    inputs: list[SpotifyId] = []
    params: SpotifyAlbumsParams = SpotifyAlbumsParams(region="de")

    def get_s3_prefix(self) -> str:
        return f"spotify/albums_{self.params.region}"


class SpotifyArtistAlbumsReleaseTypes(BaseModel):
    albums: bool = False
    singles: bool = False
    compilations: bool = False
    appears_on: bool = False

    @model_validator(mode="after")
    def any_release_group_set(self):
        if not any([self.albums, self.singles, self.compilations, self.appears_on]):
            raise ValueError(
                "At least one flag from 'album', 'single', 'compilation', and 'appears_on' must be set",
            )
        return self


class SpotifyArtistAlbumsParams(BaseModel):
    region: DataFetchingRegion
    release_types: SpotifyArtistAlbumsReleaseTypes


class SpotifyArtistAlbumsTask(SpotifyTaskBase):
    task_type: SpotifyArtistAlbumsTaskType = "artist-albums"
    inputs: list[SpotifyId] = []
    params: SpotifyArtistAlbumsParams = SpotifyArtistAlbumsParams(
        region="de",
        release_types=SpotifyArtistAlbumsReleaseTypes(
            albums=True, singles=True, compilations=True, appears_on=False
        ),
    )

    def get_s3_prefix(self) -> str:
        return f"spotify/artist_albums_{self.params.region}"


class SpotifyISRCTrackSearchParams(BaseModel):
    region: DataFetchingRegion


class SpotifyISRCTrackSearchTask(SpotifyTaskBase):
    task_type: SpotifyISRCTrackSearchTaskType = "isrc-track-search"
    inputs: list[str] = []
    params: SpotifyISRCTrackSearchParams

    def get_s3_prefix(self) -> str:
        return f"spotify/tracks_{self.params.region}"


class SpotifyPlaylistsTask(SpotifyTaskBase):
    task_type: SpotifyPlaylistsTaskType = "playlists"
    inputs: list[SpotifyId] = []
    params: None = None

    def get_s3_prefix(self) -> str:
        return "spotify/playlists"


SpotifyAPITask = (
    SpotifyTracksTask
    | SpotifyArtistsTask
    | SpotifyAlbumsTask
    | SpotifyArtistAlbumsTask
    | SpotifyISRCTrackSearchTask
    | SpotifyPlaylistsTask
)

SpotifyAPITaskParams = (
    SpotifyTracksParams
    | SpotifyAlbumsParams
    | SpotifyArtistAlbumsParams
    | SpotifyISRCTrackSearchParams
    | None
)
