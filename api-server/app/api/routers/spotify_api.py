from typing import Callable
from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession
from pydantic import BaseModel

from app.config import settings
from app.db.models import JSONValue
from app.api.dependencies.core import DBSessionDep
from app.api.utils import check_api_ban
from app.tasks.input_validation.spotify_api import (
    TracksPayload,
    TracksParams,
    ArtistsPayload,
    ArtistAlbumsPayload,
    ArtistAlbumsParams,
    AlbumsPayload,
    AlbumsParams,
    PlaylistsPayload,
    ISRCTrackSearchPayload,
    ISRCTrackSearchParams,
)
from app.tasks import create_new_task, run_in_background
from app.tasks.processing import TaskProcessor, DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel

router = APIRouter(prefix="/spotify-api")


async def create_sp_api_task[T: JSONValue](
    task_type: str,
    inputs: list[T],
    params: BaseModel | None,
    subprefix: str,
    session: AsyncDBSession,
    batch_size: int | None = None,
) -> tuple[DBTask, TaskProcessor[T]]:
    return await create_new_task(
        data_source="spotify-api",
        task_type=task_type,
        inputs=inputs,
        params=params,
        s3_bucket=settings.s3_bucket,
        s3_prefix=f"spotify/{subprefix}",
        session=session,
        batch_size=batch_size,
    )


def check_sp_api_ban(endpoint: str) -> Callable:
    # Hardcode data_source to "spotify_api"
    return check_api_ban(data_source="spotify-api", endpoint=endpoint)


@router.post("/tracks", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="tracks")
async def fetch_tracks(
    payload: TracksPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.track_ids,
        params=TracksParams(region=payload.region),
        task_type="tracks",
        subprefix=f"tracks_{payload.region}",
        session=session,
        batch_size=50,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.post("/artists", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="artists")
async def fetch_artists(
    payload: ArtistsPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.artist_ids,
        params=None,
        task_type="artists",
        subprefix="artists",
        session=session,
        batch_size=50,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.post("/artist-albums", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="artists")
async def fetch_artist_albums(
    payload: ArtistAlbumsPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.artist_ids,
        params=ArtistAlbumsParams(
            region=payload.region,
            albums=payload.albums,
            singles=payload.singles,
            compilations=payload.compilations,
            appears_on=payload.appears_on,
        ),
        task_type="artist_albums",
        subprefix=f"artist_albums_{payload.region}",
        session=session,
        batch_size=50,
    )

    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.post("/albums", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="albums")
async def fetch_albums(
    payload: AlbumsPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.album_ids,
        params=AlbumsParams(region=payload.region),
        task_type="albums",
        subprefix=f"albums_{payload.region}",
        session=session,
        batch_size=50,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.post("/playlists", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="playlists")
async def fetch_playlists(
    payload: PlaylistsPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.playlist_ids,
        params=None,
        task_type="playlists",
        subprefix="playlists",
        session=session,
        batch_size=50,
    )
    run_in_background(processor, background_tasks)

    return TaskModel.model_validate(task)


@router.post("/track-search-isrcs", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="search")
async def search_tracks_by_isrc(
    payload: ISRCTrackSearchPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_api_task(
        inputs=payload.isrcs,
        params=ISRCTrackSearchParams(region=payload.region),
        task_type="track_search_isrcs",
        subprefix=f"tracks_{payload.region}",
        session=session,
        batch_size=50,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)
