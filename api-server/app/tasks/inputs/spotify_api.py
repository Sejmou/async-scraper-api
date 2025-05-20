from pydantic import BaseModel

from typing import Literal


class SpotifyInputsBase(BaseModel):
    """
    Base class for all Spotify API task inputs.
    """

    data_source: Literal["spotify-api"] = "spotify-api"


class TracksInputs(SpotifyInputsBase):
    task_type: Literal["tracks"] = "tracks"
    inputs: list[str]


class ArtistsInputs(SpotifyInputsBase):
    task_type: Literal["artists"] = "artists"
    inputs: list[str]


class AlbumsInputs(SpotifyInputsBase):
    task_type: Literal["albums"] = "albums"
    inputs: list[str]


class ArtistAlbumsInputs(SpotifyInputsBase):
    task_type: Literal["artist-albums"] = "artist-albums"
    inputs: list[str]


class ISRCTrackSearchInputs(SpotifyInputsBase):
    task_type: Literal["isrc-track-search"] = "isrc-track-search"
    inputs: list[str]


class PlaylistsInputs(SpotifyInputsBase):
    task_type: Literal["playlists"] = "playlists"
    inputs: list[str]


SpotifyAPITaskInputs = (
    TracksInputs
    | ArtistsInputs
    | AlbumsInputs
    | ArtistAlbumsInputs
    | ISRCTrackSearchInputs
    | PlaylistsInputs
)
