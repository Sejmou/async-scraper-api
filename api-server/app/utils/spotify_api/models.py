from pydantic import BaseModel


class SpotifyAPICredentials(BaseModel):
    client_id: str
    client_secret: str
