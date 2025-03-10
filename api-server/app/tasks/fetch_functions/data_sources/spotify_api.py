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
    AlbumsParams,
    ArtistAlbumsParams,
    TracksParams,
    ISRCTrackSearchParams,
)

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

            def fetch_artist_albums(artist_id: str) -> Any:
                return spotify_api_client.artist_albums(
                    artist_id,
                    include_albums=params.albums,
                    include_singles=params.singles,
                    include_compilations=params.compilations,
                    include_appears_on=params.appears_on,
                    region=params.region,
                )

            return fetch_artist_albums

        elif task_type == "playlists":
            return spotify_api_client.playlist

        elif task_type == "isrc-track-search":
            params = convert_to_basemodel_instance_of_type(
                task_params, ISRCTrackSearchParams
            )

            def fetch_tracks_for_isrc(isrc: str) -> Any:
                return spotify_api_client.search_tracks_for_isrc(
                    isrc,
                    region=params.region,
                )

            return fetch_tracks_for_isrc


class SpotifyAPIBatchFetchFunctionFactory(DataSourceBatchFetchFunctionFactory):
    """
    A factory class for creating batch fetch functions for the Spotify API.
    """

    def create(self, task_type: str, task_params: ParamsInput) -> BatchFetchFunction:

        if not is_batch_task_type(task_type):
            raise ValueError(f"Unsupported batch task type: {task_type}")

        if task_type == "tracks":
            params = convert_to_basemodel_instance_of_type(task_params, TracksParams)

            def fetch_tracks(track_ids: list[str]) -> Any:
                return spotify_api_client.tracks(track_ids, region=params.region)

            return fetch_tracks

        elif task_type == "artists":
            return spotify_api_client.artists

        elif task_type == "albums":
            params = convert_to_basemodel_instance_of_type(task_params, AlbumsParams)

            def fetch_albums(album_ids: list[str]) -> Any:
                return spotify_api_client.albums(
                    album_ids,
                    region=params.region,
                )

            return fetch_albums
