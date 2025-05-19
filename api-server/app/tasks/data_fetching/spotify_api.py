from typing import Any, Sequence
from app.api_clients import spotify_api_client
from app.tasks.params.spotify_api import SpotifyAPITaskParams
from app.tasks.common import (
    SingleItemFetchFunction,
    BatchFetchFunction,
    FatalProcessingError,
)
from app.tasks.data_fetching import (
    SingleItemFetchFunctionResult,
    BatchFetchFunctionResult,
)
from app.utils.spotify_api import CredentialsBlockedException


def create_spotify_api_fetch_fn(
    meta: SpotifyAPITaskParams,
):
    if meta.task_type == "tracks":

        async def fetch_tracks(track_ids: Sequence[str]) -> Any:
            try:
                return await spotify_api_client.tracks(
                    track_ids,
                    region=meta.region,
                )
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return BatchFetchFunctionResult(fn=fetch_tracks, batch_size=50)
    elif meta.task_type == "artists":

        async def fetch_artists(artist_ids: Sequence[str]) -> Any:
            try:
                return await spotify_api_client.artists(artist_ids)
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return BatchFetchFunctionResult(fn=fetch_artists, batch_size=50)
    elif meta.task_type == "albums":

        async def fetch_albums(album_ids: Sequence[str]) -> Any:
            try:
                return await spotify_api_client.albums(
                    album_ids,
                    region=meta.region,
                )
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return BatchFetchFunctionResult(fn=fetch_albums, batch_size=20)
    elif meta.task_type == "artist-albums":

        async def fetch_artist_albums(artist_id: str) -> Any:
            try:
                return await spotify_api_client.artist_albums(
                    artist_id,
                    include_albums=meta.release_types.albums,
                    include_singles=meta.release_types.singles,
                    include_compilations=meta.release_types.compilations,
                    include_appears_on=meta.release_types.appears_on,
                    region=meta.region,
                )
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return SingleItemFetchFunctionResult(fn=fetch_artist_albums)

    elif meta.task_type == "playlists":

        async def fetch_playlist(playlist_id: str) -> Any:
            try:
                return await spotify_api_client.playlist(playlist_id)
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return SingleItemFetchFunctionResult(fn=fetch_playlist)
    elif meta.task_type == "isrc-track-search":

        async def fetch_tracks_for_isrc(isrc: str) -> Any:
            try:
                return await spotify_api_client.search_tracks_for_isrc(
                    isrc,
                    region=meta.region,
                )
            except CredentialsBlockedException as e:
                raise FatalProcessingError(e.message) from e

        return SingleItemFetchFunctionResult(fn=fetch_tracks_for_isrc)
