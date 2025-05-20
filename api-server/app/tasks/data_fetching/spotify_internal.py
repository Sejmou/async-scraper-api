from app.api_clients import spotify_internal_api_client
from app.tasks.params.spotify_internal import SpotifyInternalAPITaskParams
from app.tasks.common import SingleItemFetchFunctionResult


def create_spotify_internal_api_fetch_fn(
    meta: SpotifyInternalAPITaskParams,
) -> SingleItemFetchFunctionResult:
    if meta.task_type == "related-artists":
        return SingleItemFetchFunctionResult(
            fn=spotify_internal_api_client.related_artists,
        )
