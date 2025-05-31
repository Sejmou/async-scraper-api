from datetime import datetime
from pydantic import BaseModel
import aiohttp

from app.config import settings
from app.utils.spotify_api.models import SpotifyAPICredentials


class SpotifyAPIRequestMeta(BaseModel):
    url: str
    status_code: int
    sent_at: datetime
    received_at: datetime
    ip: str
    credentials: SpotifyAPICredentials


async def report_request_meta(
    request_meta: SpotifyAPIRequestMeta,
):
    meta = SpotifyAPIRequestMeta(
        url=request_meta.url,
        status_code=request_meta.status_code,
        sent_at=request_meta.sent_at,
        received_at=request_meta.received_at,
        ip=request_meta.ip,
        credentials=request_meta.credentials,
    )

    url = f"{settings.credentials_api_url}/spotify/request-meta"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=meta.model_dump_json()) as response:
                response.raise_for_status()
        except aiohttp.ClientResponseError as e:
            raise RuntimeError(
                f"Failed to report request meta: {e.status} - {e.message}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error while reporting request meta: {e}"
            ) from e
