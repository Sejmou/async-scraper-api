from pydantic import ValidationError, validate_call
from base64 import b64encode
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, Optional, List, TypeGuard, Union
from cachetools import TTLCache, cached
from logging import Logger
from app.utils.api_bans import APIBanHandler
from app.config import SpotifyAPICredentials
import aiohttp
from asyncio import sleep
from utils.request_meta import APIRequestMetaSchema, persist_request_meta_in_db
from app.config import PUBLIC_IP


class CredentialsBlockedException(Exception):
    def __init__(self, message: str, blocked_until: datetime | None = None):
        super().__init__(message)
        self.message = message
        self.blocked_until = blocked_until


def is_dict_or_none(d: Union[Dict, None]) -> TypeGuard[Optional[Dict]]:
    return isinstance(d, (dict, type(None)))


def is_list_of_dicts_or_none(
    lst: List[Union[Dict, None]],
) -> TypeGuard[List[Optional[Dict]]]:
    return all(is_dict_or_none(item) for item in lst)


def get_list_data_from_response(response: dict[str, Any], key: str):
    """
    Several endpoints in the Spotify API return a list of dictionaries (or None) in the response
    (which contains the data we are interested int), under a specific key.

    This function performs basic validation on such responses and returns the data if it is valid.
    """
    try:
        data = response[key]
    except KeyError:
        raise ValidationError(f"Expected '{key}' key not found in response.")
    if not is_list_of_dicts_or_none(data):
        raise ValidationError(
            f"Expected '{key}' in response to be a list of dictionaries."
        )
    return data


def remove_spotify_id(input_string: str) -> str:
    # Regular expression to match a Spotify 22-character ID
    id_pattern = r"[A-Za-z0-9]{22}"

    # Search for the ID in the input string
    match = re.search(id_pattern, input_string)

    if match:
        # Remove the ID from the string
        cleaned_string = input_string.replace(match.group(), "")
        return cleaned_string
    else:
        return input_string


class SpotifyAPIAccessTokenManager:
    """
    Makes sure that the access token for the Spotify API is always up-to-date and valid.
    """

    _client_id: str
    _client_secret: str
    _token_cache: TTLCache = TTLCache(maxsize=1, ttl=59 * 60)

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    def invalidate_access_token(self):
        """
        Call this whenever the access token returned by the `access_token` property is no longer valid.
        This will force a new access token to be fetched on the next access.
        """
        self._token_cache.clear()

    @property
    async def access_token(self) -> str:
        """
        Get an access token from the Spotify API using the specified client ID and secret
        (i.e. with the ['client credentials' flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)).
        """

        # using cache=self._token_cache with @cached directly on the access_token function doesn't work, hence we need this inner function
        @cached(cache=self._token_cache)
        async def get_token():
            url: str = "https://accounts.spotify.com/api/token"
            headers: dict = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {b64encode(f'{self._client_id}:{self._client_secret}'.encode()).decode()}",
            }
            data: dict = {"grant_type": "client_credentials"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    token = (await response.json())["access_token"]
                    assert isinstance(
                        token, str
                    ), f"Expected access token to be a string, but got: {token}"
                    return token

        return await get_token()


class SpotifyAPIClient:
    """
    A custom Spotify API client that fetches data from the Spotify API using provided credentials.
    """

    _last_request_overall: datetime | None = None
    _last_request_per_endpoint: Dict[str, datetime] = {}
    _timeouts_per_endpoint: Dict[str, float] = {
        "search": 15,
        "playlist": 15,
    }
    """
    Timeout between requests for specific endpoints, in seconds (e.g. value of 15 means 60/15 = 4 requests per minute)
    
    Values here have been chosen based on experience with the respective API endpoints.
    Any values not listed here will use `_default_timeout`.
    """
    _default_timeout: float = 5
    """
    The default timeout between requests for endpoints not listed in `_timeouts_per_endpoint`, in seconds.
    """

    def __init__(
        self,
        credentials: SpotifyAPICredentials,
        logger: Logger,
        ban_handler: APIBanHandler,
        global_request_timeout_override: Optional[float] = None,
    ):
        self.logger = logger
        self._token_manager = SpotifyAPIAccessTokenManager(
            credentials.client_id, credentials.client_secret
        )
        self.global_request_timeout_override = global_request_timeout_override
        self._ban_handler = ban_handler

    def _get_endpoint_name(self, endpoint_path: str) -> str:
        # for endpoints like /artists/{id}/albums, we cannot use the endpoint name as is
        # because it contains the artist ID, which is unique for each artist
        # and the "/" would create problems when accessing the credentials endpoint to get the credentials
        return remove_spotify_id(endpoint_path.replace("/", ".")).replace("..", ".")

    async def _make_request(self, endpoint_path: str, params: Optional[dict] = None):
        """
        Make a request to the Spotify API using the credentials the client was initialized with.
        """
        endpoint_name = self._get_endpoint_name(endpoint_path)
        await self._ban_handler.raise_if_blocked("spotify_api", endpoint_name)

        self.logger.debug(f"Making request to {endpoint_name} endpoint...")

        headers = {"Authorization": f"Bearer {await self._token_manager.access_token}"}
        params = params or {}

        timeout = self._get_request_timeout(endpoint_name)
        if timeout:
            self.logger.debug(
                f"Waiting {timeout} seconds before making request to {endpoint_name} endpoint..."
            )
            await sleep(timeout)
        sent_at = datetime.now(timezone.utc)
        self._last_request_per_endpoint[endpoint_name] = sent_at
        self._last_request_overall = sent_at

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.spotify.com/v1/{endpoint_path}",
                headers=headers,
                params=params,
            ) as response:
                data = await response.json()
                received_at = datetime.now(timezone.utc)

        req_meta = APIRequestMetaSchema(
            url=str(response.url),
            ip=PUBLIC_IP,
            status_code=response.status,
            sent_at=sent_at,
            received_at=received_at,
        )
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            exc: CredentialsBlockedException = CredentialsBlockedException(
                f"Spotify API endpoint '{endpoint_name}' is blocked (received 429 error), but got no RETRY-AFTER header value for some reason."
            )
            if retry_after:
                try:
                    retry_after = int(retry_after)
                    blocked_until = received_at + timedelta(seconds=retry_after)
                    details = {"retry_after": retry_after}
                    await self._ban_handler.block(
                        data_source="spotify-api",
                        endpoint=endpoint_name,
                        block_until=blocked_until,
                        details=details,
                    )
                    error_msg = f"Spotify API endpoint '{endpoint_name}' is blocked (received 429 error) until {blocked_until.isoformat()}. Got RETRY-AFTER header value: {retry_after}"
                    exc = CredentialsBlockedException(
                        error_msg,
                        blocked_until,
                    )
                except ValueError:
                    exc = CredentialsBlockedException(
                        f"Spotify API endpoint '{endpoint_name}' is blocked (received 429 error). Got unexpected/invalid RETRY-AFTER header value: {retry_after}"
                    )
                req_meta.details = {
                    "retry_after": retry_after,
                }
                raise exc
        elif response.status == 401:
            self.logger.info(
                f"Access token for endpoint {endpoint_name} expired. Invalidating currently stored access token and retrying..."
            )
            self._token_manager.invalidate_access_token()
            await persist_request_meta_in_db(req_meta)
            return await self._make_request(endpoint_path, params)

        await persist_request_meta_in_db(req_meta)

        response.raise_for_status()
        return data

    def _get_request_timeout(self, endpoint: str) -> float | None:
        last_relevant_request_at = (
            self._last_request_overall
            if self.global_request_timeout_override
            else self._last_request_per_endpoint[endpoint]
        )
        if not last_relevant_request_at:
            return None
        earliest_time_for_next_request = last_relevant_request_at + timedelta(
            seconds=self.global_request_timeout_override
            or self._timeouts_per_endpoint.get(endpoint, self._default_timeout)
        )
        seconds_to_wait = (
            earliest_time_for_next_request - datetime.now(timezone.utc)
        ).seconds
        if seconds_to_wait < 0:
            return None
        return seconds_to_wait

    @validate_call
    async def tracks(self, track_ids: List[str], region: Optional[str] = None):
        params = {"ids": ",".join(track_ids)}
        if region:
            params["market"] = region
        raw = await self._make_request(f"tracks", params=params)
        return get_list_data_from_response(raw, "tracks")

    @validate_call
    async def artists(self, artist_ids: List[str]):
        raw = await self._make_request(f"artists", params={"ids": ",".join(artist_ids)})
        return get_list_data_from_response(raw, "artists")

    @validate_call
    async def artist_albums_page(
        self,
        artist_id: str,
        offset=0,
        limit=50,
        region: Optional[str] = None,
        include_albums=True,
        include_singles=True,
        include_compilations=True,
        include_appears_on=True,
    ):
        include_groups: List[str] = []
        if include_albums:
            include_groups.append("album")
        if include_singles:
            include_groups.append("single")
        if include_compilations:
            include_groups.append("compilation")
        if include_appears_on:
            include_groups.append("appears_on")
        include_groups_str = ",".join(include_groups)
        raw = await self._make_request(
            f"artists/{artist_id}/albums",
            params={
                "offset": offset,
                "limit": limit,
                "include_groups": include_groups_str,
                "market": region,
            },
        )
        albums = get_list_data_from_response(raw, "items")
        return albums, raw["next"] != None

    @validate_call
    async def artist_albums(
        self,
        artist_id: str,
        include_albums: bool,
        include_singles: bool,
        include_compilations: bool,
        include_appears_on: bool,
        region: Optional[str] = None,
        max_offset: int | None = None,
    ):
        albums: List[Optional[Dict]] = []
        next_page = True
        offset = 0
        while (max_offset and max_offset < offset) or next_page:
            page, next_page = await self.artist_albums_page(
                artist_id,
                offset,
                include_albums=include_albums,
                include_singles=include_singles,
                include_compilations=include_compilations,
                include_appears_on=include_appears_on,
                region=region,
            )
            albums.extend(page)
            offset += len(page)
        return albums

    @validate_call
    async def albums(self, album_ids: List[str], region: Optional[str] = None):
        params = {"ids": ",".join(album_ids)}
        if region:
            params["market"] = region
        raw = await self._make_request(f"albums", params=params)
        albums = get_list_data_from_response(raw, "albums")

        # albums returned by the API only contain the first page of tracks inside the `items` of their `tracks` object
        # instead of just that first page with the pagination info (e.g. `next`, `offset`, `total`, etc.),
        # we would like to have the full list of tracks for each album under the `tracks` key
        # To achieve this, we need to fetch the full list of tracks w/ pagination and finally replace the `tracks` key in each album with that full list
        for album in albums:
            # skip over album IDs that returned no results
            if album is None:
                continue
            tracks_page = album["tracks"]
            tracks = tracks_page["items"]
            more_tracks_to_fetch = tracks_page["next"] != None
            offset = 0
            limit = 50  # up to 50 tracks can be returned per page
            while more_tracks_to_fetch:
                offset += limit
                tracks_in_page, more_tracks_to_fetch = await self.album_tracks_page(
                    album["id"], offset=offset, limit=limit, region=region
                )
                tracks.extend(tracks_in_page)

            # replace the original content of the `tracks` key with the full list of tracks
            album["tracks"] = tracks

        return albums

    @validate_call
    async def album_tracks_page(
        self, album_id: str, offset: int, region: Optional[str] = None, limit: int = 50
    ):
        params: Dict[str, Union[int, str]] = {"offset": offset, "limit": limit}
        if region:
            params["market"] = region
        raw = await self._make_request(f"albums/{album_id}/tracks", params=params)
        tracks = get_list_data_from_response(raw, "items")
        has_more_tracks = raw["next"] != None
        return tracks, has_more_tracks

    @validate_call
    async def playlist_tracks_page(
        self, playlist_id: str, offset: int, limit: int = 100
    ):
        params = {"offset": offset, "limit": limit}
        raw = await self._make_request(f"playlists/{playlist_id}/tracks", params=params)
        tracks = get_list_data_from_response(raw, "items")
        has_more_tracks = raw["next"] != None
        return tracks, has_more_tracks

    @validate_call
    async def playlist(self, playlist_id: str):
        raw = await self._make_request(f"playlists/{playlist_id}")
        if raw is None:
            return None

        assert isinstance(
            raw, dict
        ), f"Expected playlist to be a dictionary, but got: {raw}"

        # tracks are returned in pages of 100, so we need to fetch all pages to get all tracks
        tracks_page = raw["tracks"]
        # store the first page of tracks; we will extend this as needed
        tracks = tracks_page["items"]
        more_tracks_to_fetch = tracks_page["next"] != None
        limit = 100  # up to 100 tracks can be returned per page
        offset = 0
        while more_tracks_to_fetch:
            offset += limit
            tracks_in_page, more_tracks_to_fetch = await self.playlist_tracks_page(
                playlist_id, offset=offset, limit=limit
            )
            tracks.extend(tracks_in_page)

        # replace the original content of the `tracks` key with the full list of tracks
        raw["tracks"] = tracks

        return raw

    @validate_call
    async def search_tracks_for_isrc(
        self, isrc: str, region: Optional[str] = None, offset: int = 0
    ):
        # endpoint returns maximum of 50 results
        limit = 50
        raw = await self._make_request(
            f"search",
            params={
                "q": f"isrc:{isrc}",
                "type": "track",
                "limit": limit,
                "offset": offset,
                "market": region,
            },
        )
        # while very unlikely for ISRC search, we could have more than 50 results
        tracks_page = raw["tracks"]
        # store the first page of tracks; we will extend this as needed
        tracks = tracks_page["items"]
        more_tracks_to_fetch = tracks_page["next"] != None
        limit = 100  # up to 100 tracks can be returned per page
        offset = 0
        while more_tracks_to_fetch:
            offset += limit
            tracks_in_page, more_tracks_to_fetch = await self.search_tracks_for_isrc(
                isrc, region, offset=offset
            )
            tracks.extend(tracks_in_page)

        assert isinstance(
            tracks, list
        ), f"Expected found tracks for search for ISRC {isrc} to be a list, but got: {tracks}"
        assert all(
            isinstance(track, dict) for track in tracks
        ), f"Expected all found tracks for search for ISRC {isrc} to be dictionaries, but got: {tracks}"

        return tracks

    # the audio features and related artists endpoints, amongst other ones, were deactivated for regular people by Spotify with a BS 'explanation' (I hate greedy corporations lol) - RIP :(
    # https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
