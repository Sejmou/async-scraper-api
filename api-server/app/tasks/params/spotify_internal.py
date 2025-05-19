from typing import Literal
from pydantic import BaseModel


class SpotifyInternalParamsBase(BaseModel):
    """
    Base class for all Spotify internal API task parameters.
    """

    data_source: Literal["spotify-internal"] = "spotify-internal"
    """
    The data source for the task. This is always "spotify-internal".
    """


class RelatedArtistsParams(SpotifyInternalParamsBase):
    task_type: Literal["related-artists"] = "related-artists"


SpotifyInternalAPITaskParams = RelatedArtistsParams
