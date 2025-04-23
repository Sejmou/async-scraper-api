"""
NOTE: This router is mostly used for debugging my task logic. It doesn't actually call any useful API endpoints.
"""

import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import JSONValue
from app.api.dependencies.core import DBSessionDep
from app.tasks.input_validation.dummy_api import FlakyPayload
from app.tasks import create_new_task, run_in_background
from app.tasks.processing import TaskProcessor, DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.config import settings

router = APIRouter(prefix="/dummy-api")


async def create_dummy_api_task[T: JSONValue](
    task_type: str,
    inputs: list[T],
    params: BaseModel | None,
    subprefix: str,
    session: AsyncDBSession,
) -> tuple[DBTask, TaskProcessor[T]]:
    return await create_new_task(
        data_source="dummy-api",
        task_type=task_type,
        inputs=inputs,
        params=params,
        s3_prefix=f"dummy-api/{subprefix}",
        session=session,
    )


@router.post("/flaky", status_code=202, response_model=TaskModel)
async def fetch_flaky(
    payload: FlakyPayload, background_tasks: BackgroundTasks, session: DBSessionDep
):
    task, processor = await create_dummy_api_task(
        inputs=payload.inputs,
        params=payload.params,
        task_type="flaky",
        subprefix="flaky",
        session=session,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.post("/throw-above-threshold", status_code=202, response_model=TaskModel)
async def fetch_throw_above_threshold(
    payload: FlakyPayload, background_tasks: BackgroundTasks, session: DBSessionDep
):
    task, processor = await create_dummy_api_task(
        inputs=payload.inputs,
        params=payload.params,
        task_type="throw-above-threshold",
        subprefix="throw-above-threshold",
        session=session,
    )
    run_in_background(processor, background_tasks)
    return TaskModel.model_validate(task)


@router.get("/logs")
async def get_logs():
    """
    Fetch logs from the Spotify API client.
    """
    log_file_path = os.path.join(settings.api_client_log_dir, "dummy-api.log")
    if not os.path.exists(log_file_path):
        return HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        log_file_path,
        media_type="text/plain",
        filename="dummy-api-client.log",
    )
