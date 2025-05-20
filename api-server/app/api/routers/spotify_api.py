import os
from typing import Callable
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.api.dependencies.core import DBSessionDep
from app.api.utils import check_api_ban
from app.tasks.models.spotify_api import (
    SpotifyAPITaskParams,
    SpotifyTracksParams,
    SpotifyArtistAlbumsParams,
    SpotifyAlbumsParams,
    SpotifyISRCTrackSearchParams,
)
from app.tasks import create_new_task
from app.db.models import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.config import settings

router = APIRouter(prefix="/spotify-api")


async def create_sp_api_task(
    params: SpotifyAPITaskParams,
    subprefix: str,
    session: AsyncDBSession,
) -> DBTask:
    return await create_new_task(
        params=params,
        s3_prefix=f"spotify/{subprefix}",
        session=session,
    )


def check_sp_api_ban(endpoint: str) -> Callable:
    # Hardcode data_source to "spotify-api"
    return check_api_ban(data_source="spotify-api", endpoint=endpoint)


@router.post("/tracks", status_code=201, response_model=TaskModel)
@check_sp_api_ban(endpoint="tracks")
async def fetch_tracks(
    params: SpotifyTracksParams,
    session: DBSessionDep,
):
    task = await create_sp_api_task(
        params=params,
        subprefix=f"tracks_{params.region}",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.post("/artists", status_code=201, response_model=TaskModel)
@check_sp_api_ban(endpoint="artists")
async def fetch_artists(
    session: DBSessionDep,
):
    task = await create_sp_api_task(
        params=None,
        subprefix="artists",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.post("/artist-albums", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="artists")
async def fetch_artist_albums(
    params: SpotifyArtistAlbumsParams,
    session: DBSessionDep,
):

    task = await create_sp_api_task(
        params=params,
        subprefix=f"artist_albums_{params.region}",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.post("/albums", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="albums")
async def fetch_albums(
    params: SpotifyAlbumsParams,
    session: DBSessionDep,
):
    task = await create_sp_api_task(
        params=params,
        subprefix=f"albums_{params.region}",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.post("/playlists", status_code=201, response_model=TaskModel)
@check_sp_api_ban(endpoint="playlists")
async def fetch_playlists(
    session: DBSessionDep,
):
    task = await create_sp_api_task(
        params=None,
        subprefix="playlists",
        session=session,
    )

    return TaskModel.model_validate(task)


@router.post("/track-search-isrcs", status_code=202, response_model=TaskModel)
@check_sp_api_ban(endpoint="search")
async def search_tracks_by_isrc(
    params: SpotifyISRCTrackSearchParams,
    session: DBSessionDep,
):
    task = await create_sp_api_task(
        params=params,
        subprefix=f"tracks_{params.region}",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.get("/logs")
async def get_logs():
    """
    Fetch logs from the Spotify API client.
    """
    log_file_path = os.path.join(settings.api_client_log_dir, "spotify-api.log")
    if not os.path.exists(log_file_path):
        return HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        log_file_path,
        media_type="text/plain",
        filename="spotify-api-client.log",
    )
