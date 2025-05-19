from pydantic import BaseModel, model_validator

from typing import Literal


class SpotifyParamsBase(BaseModel):
    """
    Base class for all Spotify API task parameters.
    """

    data_source: Literal["spotify-api"] = "spotify-api"


DataFetchingRegion = Literal["de", "us"]


class TracksParams(SpotifyParamsBase):
    task_type: Literal["tracks"] = "tracks"
    region: DataFetchingRegion


class ArtistsParams(SpotifyParamsBase):
    task_type: Literal["artists"] = "artists"
    region: DataFetchingRegion


class AlbumsParams(SpotifyParamsBase):
    task_type: Literal["albums"] = "albums"
    region: DataFetchingRegion


class ArtistAlbumsReleaseTypes(BaseModel):
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


class ArtistAlbumsParams(SpotifyParamsBase):
    task_type: Literal["artist-albums"] = "artist-albums"
    region: DataFetchingRegion
    release_types: ArtistAlbumsReleaseTypes


class ISRCTrackSearchParams(SpotifyParamsBase):
    task_type: Literal["isrc-track-search"] = "isrc-track-search"
    region: DataFetchingRegion


class PlaylistsParams(SpotifyParamsBase):
    task_type: Literal["playlists"] = "playlists"


SpotifyAPITaskParams = (
    TracksParams
    | ArtistsParams
    | AlbumsParams
    | ArtistAlbumsParams
    | ISRCTrackSearchParams
    | PlaylistsParams
)
