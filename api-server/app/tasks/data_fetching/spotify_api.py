from typing import Any, Sequence
from app.api_clients import spotify_api_client
from app.tasks.models.spotify_api import (
    SpotifyAPITask,
)
from app.tasks.common import (
    SingleItemFetchFunctionResult,
    BatchFetchFunctionResult,
    NonFatalProcessingError,
)
from app.utils.spotify_api.client import NotFoundError


def create_spotify_api_fetch_fn(
    task: SpotifyAPITask,
):
    if task.task_type == "tracks":

        async def fetch_tracks(track_ids: Sequence[str]) -> Any:
            return await spotify_api_client.tracks(
                track_ids,
                region=task.params.region,
            )

        return BatchFetchFunctionResult(fn=fetch_tracks, batch_size=50)
    elif task.task_type == "artists":

        async def fetch_artists(artist_ids: Sequence[str]) -> Any:
            return await spotify_api_client.artists(artist_ids)

        return BatchFetchFunctionResult(fn=fetch_artists, batch_size=50)
    elif task.task_type == "albums":

        async def fetch_albums(album_ids: Sequence[str]) -> Any:
            try:
                return await spotify_api_client.albums(
                    album_ids,
                    region=task.params.region,
                )
            except NotFoundError as e:
                raise NonFatalProcessingError(
                    f"Album IDs {album_ids} not found in region {task.params.region}"
                ) from e

        return BatchFetchFunctionResult(fn=fetch_albums, batch_size=20)
    elif task.task_type == "artist-albums":

        async def fetch_artist_albums(artist_id: str) -> Any:
            try:
                return await spotify_api_client.artist_albums(
                    artist_id,
                    include_albums=task.params.release_types.albums,
                    include_singles=task.params.release_types.singles,
                    include_compilations=task.params.release_types.compilations,
                    include_appears_on=task.params.release_types.appears_on,
                    region=task.params.region,
                )
            except NotFoundError as e:
                raise NonFatalProcessingError(
                    f"No matching releases found for artist ID {artist_id} (region: {task.params.region}, release types: {task.params.release_types})"
                ) from e

        return SingleItemFetchFunctionResult(fn=fetch_artist_albums)

    elif task.task_type == "playlists":

        async def fetch_playlist(playlist_id: str) -> Any:
            try:
                return await spotify_api_client.playlist(playlist_id)
            except NotFoundError as e:
                raise NonFatalProcessingError(
                    f"No playlist found for ID {playlist_id}"
                ) from e

        return SingleItemFetchFunctionResult(fn=fetch_playlist)
    elif task.task_type == "isrc-track-search":

        async def fetch_tracks_for_isrc(isrc: str) -> Any:
            try:
                return await spotify_api_client.search_tracks_for_isrc(
                    isrc,
                    region=task.params.region,
                )
            except NotFoundError as e:
                raise NonFatalProcessingError(
                    f"No tracks found for ISRC {isrc} in region {task.params.region}"
                ) from e

        return SingleItemFetchFunctionResult(fn=fetch_tracks_for_isrc)
