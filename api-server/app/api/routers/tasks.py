from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from app.api.dependencies.core import DBSessionDep
from app.db.models import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.tasks.progress.public_models import TaskProgress, TaskProgressDetails
from app.tasks.progress import TaskProgressTracker

router = APIRouter(prefix="/tasks")


@router.get("/", response_model=Page[TaskModel])
async def tasks(session: DBSessionDep):
    query = (
        select(DBTask)
        .options(joinedload(DBTask.file_uploads))
        .order_by(DBTask.created_at.desc())
    )
    return await paginate(session, query)


@router.get("/{task_id}", response_model=TaskModel)
async def task(task_id: int, session: DBSessionDep):
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskModel.model_validate(task)


@router.get("/{task_id}/progress", response_model=TaskProgress)
async def task_progress(task_id: int, session: DBSessionDep):
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tracker = TaskProgressTracker(task_id)
    return await tracker.get_progress()


@router.get("/{task_id}/progress/details", response_model=TaskProgressDetails)
async def task_progress_details(task_id: int, session: DBSessionDep):
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tracker = TaskProgressTracker(task_id)
    return await tracker.get_progress_details()
