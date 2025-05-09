from typing import Any, Literal, get_args, TypeGuard

from app.tasks.fetch_functions.common import (
    DataSourceSingleItemFetchFunctionFactory,
    DataSourceBatchFetchFunctionFactory,
    SingleItemFetchFunction,
    BatchFetchFunction,
    ParamsInput,
    convert_to_basemodel_instance_of_type,
)
from app.api_clients import spotify_api_client
from app.tasks.input_validation.spotify_api import (
    RegionSpecificParams,
    ArtistAlbumsParams,
)
from app.tasks.processing import FatalProcessingError
from utils.spotify_api import CredentialsBlockedException

type SequentialTask = Literal["artist-albums", "playlists", "isrc-track-search"]
type BatchTask = Literal["tracks", "artists", "albums"]


def is_sequential_task_type(input: str) -> TypeGuard[SequentialTask]:
    return input in get_args(SequentialTask.__value__)


def is_batch_task_type(input: str) -> TypeGuard[BatchTask]:
    return input in get_args(BatchTask.__value__)


class SpotifyAPISingleItemFetchFunctionFactory(
    DataSourceSingleItemFetchFunctionFactory
):
    """
    A factory class for creating single-item fetch functions for the Spotify API.
    """

    def create(
        self, task_type: str, task_params: ParamsInput
    ) -> SingleItemFetchFunction:

        if not is_sequential_task_type(task_type):
            raise ValueError(f"Unsupported sequential task type: {task_type}")

        if task_type == "artist-albums":
            params = convert_to_basemodel_instance_of_type(
                task_params, ArtistAlbumsParams
            )

            async def fetch_artist_albums(artist_id: str) -> Any:
                try:
                    return await spotify_api_client.artist_albums(
                        artist_id,
                        include_albums=params.release_types.albums,
                        include_singles=params.release_types.singles,
                        include_compilations=params.release_types.compilations,
                        include_appears_on=params.release_types.appears_on,
                        region=params.region,
                    )
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_artist_albums

        elif task_type == "playlists":

            async def fetch_playlists(playlist_id: str) -> Any:
                try:
                    return await spotify_api_client.playlist(playlist_id)
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_playlists

        elif task_type == "isrc-track-search":
            params = convert_to_basemodel_instance_of_type(
                task_params, RegionSpecificParams
            )

            async def fetch_tracks_for_isrc(isrc: str) -> Any:
                try:
                    return await spotify_api_client.search_tracks_for_isrc(
                        isrc,
                        region=params.region,
                    )
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_tracks_for_isrc


class SpotifyAPIBatchFetchFunctionFactory(DataSourceBatchFetchFunctionFactory):
    """
    A factory class for creating batch fetch functions for the Spotify API.
    """

    def create(self, task_type: str, task_params: ParamsInput) -> BatchFetchFunction:
        if not is_batch_task_type(task_type):
            raise ValueError(f"Unsupported batch task type: {task_type}")

        if task_type == "tracks":
            params = convert_to_basemodel_instance_of_type(
                task_params, RegionSpecificParams
            )

            async def fetch_tracks(track_ids: list[str]) -> Any:
                try:
                    return await spotify_api_client.tracks(
                        track_ids,
                        region=params.region,
                    )
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_tracks

        elif task_type == "artists":

            async def fetch_artists(artist_ids: list[str]) -> Any:
                try:
                    return await spotify_api_client.artists(artist_ids)
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_artists

        elif task_type == "albums":
            params = convert_to_basemodel_instance_of_type(
                task_params, RegionSpecificParams
            )

            async def fetch_albums(album_ids: list[str]) -> Any:
                try:
                    return await spotify_api_client.albums(
                        album_ids,
                        region=params.region,
                    )
                except CredentialsBlockedException as e:
                    raise FatalProcessingError(e.message) from e

            return fetch_albums
