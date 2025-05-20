"""
NOTE: This router is mostly used for debugging my task logic. It doesn't actually call any useful API endpoints.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.api.dependencies.core import DBSessionDep
from app.tasks.models.dummy_api import (
    DummyAPITaskParams,
    DummyAPIFlakyParams,
    DummyAPIThrowAboveThresholdParams,
)
from app.tasks import create_new_task
from app.db.models import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.config import settings

router = APIRouter(prefix="/dummy-api")


async def create_dummy_api_task(
    params: DummyAPITaskParams,
    subprefix: str,
    session: AsyncDBSession,
) -> DBTask:
    return await create_new_task(
        params=params,
        s3_prefix=f"dummy-api/{subprefix}",
        session=session,
    )


@router.post("/flaky", status_code=201, response_model=TaskModel)
async def fetch_flaky(params: DummyAPIFlakyParams, session: DBSessionDep):
    task = await create_dummy_api_task(
        params=params,
        subprefix="flaky",
        session=session,
    )
    return TaskModel.model_validate(task)


@router.post("/throw-above-threshold", status_code=201, response_model=TaskModel)
async def fetch_throw_above_threshold(
    params: DummyAPIThrowAboveThresholdParams,
    session: DBSessionDep,
):
    task = await create_dummy_api_task(
        params=params,
        subprefix="throw-above-threshold",
        session=session,
    )
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
