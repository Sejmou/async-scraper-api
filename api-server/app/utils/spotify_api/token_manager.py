from datetime import datetime, timedelta, timezone
from base64 import b64encode
from typing import Awaitable, Callable
from app.utils.spotify_api.models import SpotifyAPICredentials
import aiohttp


class SpotifyAPIAccessTokenManager:
    """
    Makes sure that the access token for the Spotify API is always up-to-date and valid.
    """

    _token: str | None = None
    _token_expires_at: datetime = datetime.now(timezone.utc)

    def __init__(
        self, credential_getter: Callable[[], Awaitable[SpotifyAPICredentials]]
    ):
        self._get_credentials = credential_getter

    def invalidate_access_token(self):
        """
        Call this whenever the access token returned by the `access_token` property is no longer valid.
        This will force a new access token to be fetched on the next access.
        """
        self._token = None
        self._token_expires_at = datetime.now(timezone.utc)

    @property
    async def access_token(self) -> str:
        """
        Get an access token from the Spotify API using the specified client ID and secret
        (i.e. with the ['client credentials' flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)).
        """
        if self._token and self._token_expires_at > (
            datetime.now(timezone.utc) + timedelta(seconds=60)
        ):
            return self._token

        url: str = "https://accounts.spotify.com/api/token"
        creds = await self._get_credentials()
        headers: dict = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {b64encode(f'{creds.client_id}:{creds.client_secret}'.encode()).decode()}",
        }
        data: dict = {"grant_type": "client_credentials"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()
                resp_json = await response.json()
                token = resp_json["access_token"]
                expires_in = resp_json["expires_in"]
                assert isinstance(
                    token, str
                ), f"Expected access token to be a string, but got: {token}"
                self._token = token
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )
                return token
