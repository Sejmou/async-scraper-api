from typing import Annotated, Literal
from pydantic import BaseModel, Field, model_validator


# shared params for tasks that require a region to be specified
class RegionSpecificParams(BaseModel):
    region: Literal["de", "us"] | None = None


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


class ArtistAlbumsParams(BaseModel):
    release_types: ArtistAlbumsReleaseTypes
    region: Literal["de", "us"] | None = None


class TracksPayload(BaseModel):
    task_type: Literal["tracks"] = "tracks"
    inputs: list[str]
    params: RegionSpecificParams


class ArtistsPayload(BaseModel):
    task_type: Literal["artists"] = "artists"
    inputs: list[str]


class AlbumsPayload(BaseModel):
    task_type: Literal["albums"] = "albums"
    inputs: list[str]
    params: RegionSpecificParams


class ArtistAlbumsPayload(BaseModel):
    task_type: Literal["artist_albums"] = "artist_albums"
    inputs: list[str]
    params: ArtistAlbumsParams


class PlaylistsPayload(BaseModel):
    task_type: Literal["playlists"] = "playlists"
    inputs: list[str]


class ISRCTrackSearchPayload(BaseModel):
    task_type: Literal["isrc_track_search"] = "isrc_track_search"
    inputs: list[str]
    params: RegionSpecificParams


SpotifyApiTaskPayload = Annotated[
    TracksPayload
    | ArtistsPayload
    | AlbumsPayload
    | ArtistAlbumsPayload
    | PlaylistsPayload
    | ISRCTrackSearchPayload,
    Field(discriminator="task_type"),
]


class SpotifyApiTask(BaseModel):
    data_source: Literal["spotify_api"] = "spotify_api"
    payload: SpotifyApiTaskPayload
