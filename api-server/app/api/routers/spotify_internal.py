import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import JSONValue
from app.api.dependencies.core import DBSessionDep
from app.tasks.input_validation.spotify_internal import RelatedArtistsPayload
from app.tasks import create_new_task, run_in_background
from app.tasks.processing import TaskProcessor, DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.config import settings

router = APIRouter(prefix="/spotify-internal")


async def create_sp_internal_task[T: JSONValue](
    task_type: str,
    inputs: list[T],
    params: BaseModel | None,
    subprefix: str,
    session: AsyncDBSession,
) -> tuple[DBTask, TaskProcessor[T]]:
    return await create_new_task(
        data_source="spotify-internal",
        task_type=task_type,
        inputs=inputs,
        params=params,
        s3_prefix=f"spotify/internal_apis/{subprefix}",
        session=session,
    )


@router.post("/related-artists", status_code=202)
async def fetch_related_artists(
    payload: RelatedArtistsPayload,
    background_tasks: BackgroundTasks,
    session: DBSessionDep,
):
    task, processor = await create_sp_internal_task(
        inputs=payload.inputs,
        params=None,
        task_type="related_artists",
        subprefix=f"related_artists",
        session=session,
    )
    run_in_background(processor, background_tasks)
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
