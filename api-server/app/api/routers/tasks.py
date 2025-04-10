import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.api.dependencies.core import DBSessionDep
from app.db.models import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel
from app.tasks import get_task_processor, run_in_background
from app.tasks.progress.public_models import TaskProgress, TaskProgressDetails
from app.tasks.progress import TaskProgressTracker
from app.config import settings, app_logger

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


@router.post("/{task_id}/pause", response_model=TaskModel)
async def pause_task(task_id: int, session: DBSessionDep):
    """
    Pause a task processor with the given ID.
    """
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if task:
        if task.status == "error":
            raise HTTPException(status_code=400, detail="Task is in error state")
        if task.status == "done":
            raise HTTPException(status_code=400, detail="Task is already done")
        if task.status == "pausing":
            raise HTTPException(status_code=400, detail="Task is already pausing")
        task.status = "pausing"
        await session.commit()
        processor = get_task_processor(task)
        app_logger.info(f"Pausing processor for task ID {task_id}...")
        processor.pause()
        return TaskModel.model_validate(task)
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/resume", response_model=TaskModel)
async def resume_task(
    task_id: int, background_tasks: BackgroundTasks, session: DBSessionDep
):
    """
    Resume a task processor with the given ID.
    """
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if task:
        if task.status == "done":
            raise HTTPException(status_code=400, detail="Task is already done")
        if task.status == "pending":
            raise HTTPException(
                status_code=400, detail="Task is already resuming (pending)"
            )
        if task.status == "running":
            raise HTTPException(status_code=400, detail="Task is already running")
        task.status = "pending"
        await session.commit()
        processor = get_task_processor(task)
        app_logger.info(f"Resuming processor for task ID {task_id}...")
        run_in_background(processor, background_tasks)
        return TaskModel.model_validate(task)
    else:
        raise HTTPException(status_code=404, detail="Task not found")


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


@router.get("/{task_id}/logs")
async def task_logs(task_id: int, session: DBSessionDep):
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_path = os.path.join(settings.task_log_dir, f"{task_id}.log")
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        task_path,
        media_type="text/plain",
        filename=f"{task_id}.log",
    )
