from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import JSONValue
from app.api.dependencies.core import DBSessionDep
from app.tasks.input_validation.spotify_internal import RelatedArtistsPayload
from app.tasks import create_new_task, run_in_background
from app.tasks.processing import TaskProcessor, DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel

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
