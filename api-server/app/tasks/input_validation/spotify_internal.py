from pydantic import BaseModel


class RelatedArtistsPayload(BaseModel):
    inputs: list[str]
