from logging import Logger
from rnet import Impersonate, Client
from nodriver.cdp.network import Request
from urllib.parse import ParseResult, urlencode, urlparse, urlunparse, parse_qs
import json

from app.utils.nodriver import get_spotify_related_artists_request_blueprint


class SpotifyInternalAPIClient:
    _related_artists_blueprint: Request | None = None
    next_call_at: float | None = None

    def __init__(self, logger: Logger):
        self._logger = logger
        self._client = Client(impersonate=Impersonate.Chrome134)

    async def related_artists(self, artist_id: str) -> dict:
        self._logger.debug(f"Fetching related artists for artist ID {artist_id}")
        if not self._related_artists_blueprint:
            self._related_artists_blueprint = (
                await get_spotify_related_artists_request_blueprint(
                    artist_id, self._logger
                )
            )
        original_url = self._related_artists_blueprint.url
        parse_res = urlparse(original_url)
        query = parse_qs(parse_res.query)
        query["variables"] = [json.dumps({"uri": f"spotify:artist:{artist_id}"})]
        new_query_string = urlencode(query, doseq=True)
        new_parse_res = ParseResult(
            fragment=parse_res.fragment,
            netloc=parse_res.netloc,
            path=parse_res.path,
            params=parse_res.params,
            query=new_query_string,
            scheme=parse_res.scheme,
        )
        new_url = urlunparse(new_parse_res)
        self._logger.debug(f"Making request to {new_url}")

        resp = await self._client.get(
            new_url,
            headers=self._related_artists_blueprint.headers,
        )
        self._logger.debug(f"Got response with status {resp.status}:")
        if resp.status != 200:
            self._logger.error(
                f"Failed to get related artists for artist ID {artist_id}"
            )
            data = await resp.text()
            self._logger.error(f"Status: {resp.status}, Response: {data}")
            raise Exception(f"Failed to get related artists for artist ID {artist_id}")
        data = await resp.json()
        return data
