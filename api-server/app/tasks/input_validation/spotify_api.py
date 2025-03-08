from typing import Literal
from pydantic import BaseModel, model_validator


# types of inputs that are used for scraper tasks
class TracksInputItems(BaseModel):
    track_ids: list[str]


class ArtistsInputItems(BaseModel):
    artist_ids: list[str]


class AlbumsInputItems(BaseModel):
    album_ids: list[str]


class PlaylistsInputItems(BaseModel):
    playlist_ids: list[str]


class ISRCSInputItems(BaseModel):
    isrcs: list[str]


# shared params for tasks that require a region to be specified
class RegionSpecificParams(BaseModel):
    region: Literal["de", "us"] | None = None


# specific params for different types of tasks
class TracksParams(RegionSpecificParams):
    pass


class AlbumsParams(RegionSpecificParams):
    pass


class ArtistAlbumsParams(RegionSpecificParams):
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


class ISRCTrackSearchParams(RegionSpecificParams):
    pass


# payloads for the different types of tasks (combination of input items and, optionally, task params - if params exist, model inherts from both input items and params classes)
class TracksPayload(TracksInputItems, TracksParams):
    pass


class ArtistsPayload(ArtistsInputItems):
    pass


class AlbumsPayload(AlbumsInputItems, AlbumsParams):
    pass


class ArtistAlbumsPayload(ArtistsInputItems, ArtistAlbumsParams):
    pass


class PlaylistsPayload(PlaylistsInputItems):
    pass


class ISRCTrackSearchPayload(ISRCSInputItems, ISRCTrackSearchParams):
    pass
