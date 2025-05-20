import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.api.dependencies.core import DBSessionDep
from app.tasks.models.params.spotify_internal import (
    SpotifyInternalAPITaskParams,
    RelatedArtistsParams,
)
from app.tasks import create_new_task
from app.tasks.processing import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.config import settings

router = APIRouter(prefix="/spotify-internal")


async def create_sp_internal_task(
    params: SpotifyInternalAPITaskParams,
    subprefix: str,
    session: AsyncDBSession,
) -> DBTask:
    return await create_new_task(
        params=params,
        s3_prefix=f"spotify/internal_apis/{subprefix}",
        session=session,
    )


@router.post("/related-artists", status_code=201, response_model=TaskModel)
async def fetch_related_artists(
    params: RelatedArtistsParams,
    session: DBSessionDep,
):
    task = await create_sp_internal_task(
        params=params,
        subprefix=f"related_artists",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.get("/logs")
async def get_logs():
    """
    Fetch logs from the Spotify API client.
    """
    log_file_path = os.path.join(settings.api_client_log_dir, "spotify-internal.log")
    if not os.path.exists(log_file_path):
        return HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        log_file_path,
        media_type="text/plain",
        filename="spotify-internal-api-client.log",
    )
