from app.api_clients import spotify_internal_api_client
from app.tasks.models.spotify_internal import SpotifyInternalAPITask
from app.tasks.common import SingleItemFetchFunctionResult


def create_spotify_internal_api_fetch_fn(
    task: SpotifyInternalAPITask,
) -> SingleItemFetchFunctionResult:
    if task.task_type == "related-artists":
        return SingleItemFetchFunctionResult(
            fn=spotify_internal_api_client.related_artists,
        )
