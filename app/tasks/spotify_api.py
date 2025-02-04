from pydantic import BaseModel
from app.db.models import DataFetchingTask
from app.tasks import DataSourceTaskExecutors, TaskExecutor


class SpotifyApiTaskExecutors(DataSourceTaskExecutors):
    tracks: TaskExecutor


async def fetch_spotify_tracks(task: DataFetchingTask):
    pass


spotify_api_task_executors: SpotifyApiTaskExecutors = SpotifyApiTaskExecutors(
    tracks=fetch_spotify_tracks
)
