from typing import Literal
from pydantic import BaseModel


class SpotifyInternalInputsBase(BaseModel):
    """
    Base class for all Spotify internal API task inputs.
    """

    data_source: Literal["spotify-internal"] = "spotify-internal"
    """
    The data source for the task. This is always "spotify-internal".
    """


class RelatedArtistsInputs(SpotifyInternalInputsBase):
    task_type: Literal["related-artists"] = "related-artists"
    inputs: list[str]


SpotifyInternalAPITaskInputs = RelatedArtistsInputs
