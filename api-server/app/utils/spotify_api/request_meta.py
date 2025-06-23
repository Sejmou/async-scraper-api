from asyncio import sleep
from datetime import datetime
from pydantic import BaseModel
import aiohttp

from app.config import settings
from app.utils.spotify_api.models import SpotifyAPICredentials

MAX_RETRIES = 4
"""
The maximum number of retries for reporting request meta if the initial attempt fails for any reason.
"""


class SpotifyAPIRequestMeta(BaseModel):
    url: str
    status_code: int
    sent_at: datetime
    received_at: datetime
    ip: str
    credentials: SpotifyAPICredentials


async def _make_request_meta_reporting_request(
    meta: SpotifyAPIRequestMeta,
):
    url = f"{settings.credentials_api_url}/spotify/request-meta"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=meta.model_dump(mode="json")) as response:
                response.raise_for_status()
        except aiohttp.ClientResponseError as e:
            raise RuntimeError(
                f"Failed to report request meta: {e.status} - {e.message}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error while reporting request meta: {e}"
            ) from e


async def report_request_meta(request_meta: SpotifyAPIRequestMeta):
    meta = SpotifyAPIRequestMeta(
        url=request_meta.url,
        status_code=request_meta.status_code,
        sent_at=request_meta.sent_at,
        received_at=request_meta.received_at,
        ip=request_meta.ip,
        credentials=request_meta.credentials,
    )
    failed_attempts = 0
    while failed_attempts < MAX_RETRIES:
        try:
            await _make_request_meta_reporting_request(meta)
            return
        except RuntimeError as e:
            failed_attempts += 1
            if failed_attempts >= MAX_RETRIES:
                raise RuntimeError(
                    f"Failed to report request meta after {MAX_RETRIES} attempts: {e}"
                ) from e
            # Exponential backoff before retrying
            await sleep(2**failed_attempts)
