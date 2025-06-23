from dataclasses import dataclass
import random
from pydantic import validate_call
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional, Sequence, Union
from logging import Logger
import aiohttp
from asyncio import sleep

from app.config import PUBLIC_IP
from app.utils.spotify_api.models import SpotifyAPICredentials
from app.utils.spotify_api.request_meta import (
    SpotifyAPIRequestMeta,
    report_request_meta,
)
from app.utils.spotify_api.helpers import get_list_data_from_response, remove_spotify_id
from app.utils.spotify_api.token_manager import SpotifyAPIAccessTokenManager


class CredentialsBlockedException(Exception):
    def __init__(self, message: str, blocked_until: datetime | None = None):
        super().__init__(message)
        self.message = message
        self.blocked_until = blocked_until


@dataclass
class SuccessResult:
    data: Any
    status: Literal["success"] = "success"


@dataclass
class CredentialsExpiredResult:
    status: Literal["credentials_expired"] = "credentials_expired"


@dataclass
class CredentialsBlockedResult:
    error_msg: str
    retry_after: int | None = None
    status: Literal["credentials_blocked"] = "credentials_blocked"
    blocked_until: datetime | None = None


@dataclass
class NotFoundResult:
    msg: str
    status: Literal["not_found"] = "not_found"


@dataclass
class BadGatewayResult:
    """
    For 502 Bad Gateway errors which happen occasionally (Spotify API is not perfectly reliable)
    """

    msg: str
    status: Literal["bad_gateway"] = "bad_gateway"


MAX_502_ATTEMPTS = 3
"""
Maximum number of attempts to retry a request that returned a 502 Bad Gateway error.
"""


@dataclass
class UnexpectedErrorCodeResult:
    msg: str
    status_code: int
    status: Literal["unexpected-error"] = "unexpected-error"


class UnexpectedResponseCodeError(Exception):
    status_code: int
    message: str

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnexpectedResponseDataError(Exception):
    pass


class CredentialFetchingError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ServiceUnavailableError(Exception):
    """
    Exception raised when the Spotify API returns a 502 Bad Gateway error after multiple attempts to retry the request.
    """

    pass


class SpotifyAPIClient:
    """
    A custom Spotify API client that fetches data from the Spotify API using provided credentials.
    """

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

    _credentials: SpotifyAPICredentials | None = None
    _requests_made_with_current_credentials: int = 0
    _max_requests_with_current_credentials: int = random.randint(2500, 5000)
    """
    A non-negative integer specifying the maximum number of requests that can be made with the current credentials before they are swapped out for new ones.

    This should preferrably be a not too big, random number, so that it shouldn't be as likely to get blocked by Spotify (assumption: the more regular things look, the more likely we are to get blocked).
    """

    def __init__(
        self,
        credentials_api_url: str,
        logger: Logger,
    ):
        self.logger = logger
        self._credentials_api_url = credentials_api_url
        self._token_manager = SpotifyAPIAccessTokenManager(self.get_credentials)

    def _get_endpoint_name(self, endpoint_path: str) -> str:
        # for endpoints like /artists/{id}/albums, we cannot use the endpoint name as is
        # because it contains the artist ID, which is unique for each artist
        # and the "/" would create problems when accessing the credentials endpoint to get the credentials
        return remove_spotify_id(endpoint_path.replace("/", ".")).replace("..", ".")

    async def get_credentials(self) -> SpotifyAPICredentials:
        if (
            self._credentials
            and not self._requests_made_with_current_credentials
            >= self._max_requests_with_current_credentials
        ):
            return self._credentials

        url = f"{self._credentials_api_url}/spotify/account"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if not isinstance(data, dict):
                        raise CredentialFetchingError(
                            f"Could not fetch Spotify API credentials: expected response to be a dictionary, but got: {data}"
                        )
                    self._credentials = SpotifyAPICredentials(**data)
                    self._token_manager.invalidate_access_token()
                    self._requests_made_with_current_credentials = 0
                    self._max_requests_with_current_credentials = random.randint(
                        2500, 5000
                    )
                    self.logger.info(
                        f"Got new Spotify API credentials (client ID: {self._credentials.client_id}). Will swap after {self._max_requests_with_current_credentials} requests."
                    )
                    return self._credentials
        except aiohttp.ClientResponseError as e:
            raise CredentialFetchingError(
                f"Could not fetch Spotify API credentials: {e.status} - {e.message}"
            ) from e
        except Exception as e:
            raise CredentialFetchingError(
                f"Unexpected error while fetching Spotify API credentials: {e}"
            ) from e

    async def _make_request(
        self,
        endpoint_path: str,
        params: Optional[dict] = None,
        # only relevant in case of Bad Gateway responses. For each failed attempt, this function will be called again with same params, but increased attempt_number; once max_attempts is reached, an exception will be raised
        attempt_number=1,
    ) -> dict:
        """
        Make a request to the Spotify API using the credentials the client was initialized with.
        """
        endpoint_name = self._get_endpoint_name(endpoint_path)

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

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.spotify.com/v1/{endpoint_path}",
                headers=headers,
                params=params,
            ) as response:
                received_at = datetime.now(timezone.utc)
                req_meta = SpotifyAPIRequestMeta(
                    url=str(response.url),
                    ip=PUBLIC_IP,
                    status_code=response.status,
                    sent_at=sent_at,
                    received_at=received_at,
                    credentials=await self.get_credentials(),
                )

                res = await self._parse_response(response, req_meta, endpoint_name)
                try:
                    await report_request_meta(req_meta)
                except Exception as e:
                    if req_meta.status_code != 200:
                        raise e
                    self.logger.warning(
                        f"Failed to report metadata for request to {endpoint_name} endpoint with 200 status code: {e}"
                    )

                if res.status == "success":
                    data = res.data
                    if not isinstance(data, dict):
                        raise UnexpectedResponseDataError(
                            f"Expected response data from endpoint {endpoint_name} to be a dictionary, but got: {data}"
                        )
                    return data

                elif res.status == "credentials_expired":
                    self.logger.info(
                        f"Access token for endpoint {endpoint_name} expired. Invalidating currently stored access token and retrying..."
                    )
                    self._token_manager.invalidate_access_token()
                    return await self._make_request(endpoint_path, params)

                elif res.status == "credentials_blocked":
                    self.logger.error(
                        f"API credentials for endpoint {endpoint_name} are blocked: {res.error_msg}"
                    )

                    # make sure credentials and associated access token are not used anymore
                    self._credentials = None
                    self._token_manager.invalidate_access_token()

                    raise CredentialsBlockedException(
                        message=res.error_msg,
                        blocked_until=res.blocked_until,
                    )

                elif res.status == "not_found":
                    self.logger.warning(res.msg)
                    raise NotFoundError(res.msg)

                elif res.status == "bad_gateway":
                    self.logger.warning(res.msg)

                    if attempt_number >= MAX_502_ATTEMPTS:
                        raise ServiceUnavailableError(
                            f"Request to {endpoint_name} endpoint failed with 502 Bad Gateway error after {MAX_502_ATTEMPTS} attempts."
                        )

                    timeout = (
                        self._get_request_timeout(endpoint_name)
                        or self._default_timeout
                    )
                    sleep_time = timeout * attempt_number
                    self.logger.info(
                        f"Retrying request to {endpoint_name} endpoint in {sleep_time:.2f} seconds (attempt {attempt_number + 1} of {MAX_502_ATTEMPTS})..."
                    )
                    await sleep(timeout**attempt_number)

                    return await self._make_request(
                        endpoint_path, params=params, attempt_number=attempt_number + 1
                    )

                elif res.status == "unexpected-error":
                    self.logger.error(res.msg)
                    raise UnexpectedResponseCodeError(
                        message=f"Unexpected response from Spotify API: {res.msg}",
                        status_code=res.status_code,
                    )

                else:
                    # static type checkers aren't smart enough to understand that the above conditions cover all possible cases, so we need this as well
                    raise Exception("Got impossible result")

    async def _parse_response(
        self,
        response: aiohttp.ClientResponse,
        req_meta: SpotifyAPIRequestMeta,
        endpoint_name: str,
    ) -> (
        SuccessResult
        | CredentialsBlockedResult
        | CredentialsExpiredResult
        | NotFoundResult
        | BadGatewayResult
        | UnexpectedErrorCodeResult
    ):
        """
        Parse the response from the Spotify API and return a specific kind of result object, depending on the response status code.
        """
        if response.status == 429:
            blocked_until: datetime | None = None
            retry_after = response.headers.get("Retry-After")
            error_msg = f"Got HTTP error response with code 429 (Too Many Requests) and response body: {await response.text()}"
            if retry_after:
                try:
                    retry_after = int(retry_after)
                    blocked_until = req_meta.received_at + timedelta(
                        seconds=retry_after
                    )
                    error_msg = f"Got HTTP error response with code 429 (Too Many Requests) and RETRY-AFTER header value: {retry_after} -> '{endpoint_name}' endpoint is blocked until (at least) {blocked_until.isoformat()}."
                except ValueError:
                    error_msg = f"Got HTTP error response with code 429 (Too Many Requests) and RETRY-AFTER header value: {retry_after} -> '{endpoint_name}' is blocked."
            return CredentialsBlockedResult(
                error_msg=error_msg, blocked_until=blocked_until
            )
        elif response.status == 401:
            return CredentialsExpiredResult()
        elif response.status == 404:
            return NotFoundResult(
                msg=f"Request to '{endpoint_name}' endpoint (URL: {req_meta.url}) returned 404."
            )
        elif response.status == 502:
            return BadGatewayResult(
                msg=f"Request to '{endpoint_name}' endpoint (URL: {req_meta.url}) returned 502 Bad Gateway error."
            )
        elif not response.ok:
            return UnexpectedErrorCodeResult(
                msg=f"Request to '{endpoint_name}' endpoint failed with HTTP error {response.status} and body: {await response.text()}",
                status_code=response.status,
            )

        data = await response.json()
        return SuccessResult(data=data)

    def _get_request_timeout(self, endpoint: str) -> float | None:
        last_relevant_request_at = self._last_request_per_endpoint.get(endpoint)
        if not last_relevant_request_at:
            return None
        earliest_time_for_next_request = last_relevant_request_at + timedelta(
            seconds=self._timeouts_per_endpoint.get(endpoint, self._default_timeout)
        )
        seconds_to_wait = (
            earliest_time_for_next_request - datetime.now(timezone.utc)
        ).total_seconds()
        if seconds_to_wait < 0:
            return None
        return seconds_to_wait

    @validate_call
    async def tracks(self, track_ids: Sequence[str], region: Optional[str] = None):
        params = {"ids": ",".join(track_ids)}
        if region:
            params["market"] = region
        raw = await self._make_request(f"tracks", params=params)
        return get_list_data_from_response(raw, "tracks")

    @validate_call
    async def artists(self, artist_ids: Sequence[str]):
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
        include_groups: list[str] = []
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
        albums: list[Optional[Dict]] = []
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
    async def albums(self, album_ids: Sequence[str], region: Optional[str] = None):
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
