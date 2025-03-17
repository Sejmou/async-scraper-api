from typing import Literal
from pydantic import BaseModel, model_validator


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
    inputs: list[str]
    params: RegionSpecificParams


class ArtistsPayload(BaseModel):
    inputs: list[str]


class AlbumsPayload(BaseModel):
    inputs: list[str]
    params: RegionSpecificParams


class ArtistAlbumsPayload(BaseModel):
    inputs: list[str]
    params: ArtistAlbumsParams


class PlaylistsPayload(BaseModel):
    inputs: list[str]


class ISRCTrackSearchPayload(BaseModel):
    inputs: list[str]
    params: RegionSpecificParams
