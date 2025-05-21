import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.config import settings
from app.api.dependencies.core import DBSessionDep
from app.db.models import (
    DATA_SOURCES,
    DataFetchingTask as DBTask,
    DataSource,
    JSONValue,
)
from app.api.models import DataFetchingTask as TaskModel
from app.tasks import create_new_task, get_task_processor, run_in_background
from app.tasks.input_validation import InvalidTaskInputsError, parse_task_inputs
from app.tasks.models import TaskExecutionMetaModel
from app.tasks.progress.public_models import TaskProgress, TaskProgressDetails
from app.tasks.progress import TaskProgressTracker
from app.config import TASK_LOG_DIR, TASK_PROGRESS_DB_DIR, app_logger
from app.tasks.queue_item_management import (
    QueueType,
    TaskQueueItemManager,
)
from app.api.utils.logs import download_logs

router = APIRouter(prefix="/tasks")


def create_task_queue_item_manager(task_id: int) -> TaskQueueItemManager:
    """
    Create a TaskQueueItemManager instance with the proper database path, inferred from settings.
    """
    return TaskQueueItemManager(task_id=task_id, db_dir=TASK_PROGRESS_DB_DIR)


@router.get("/data-sources")
def get_data_sources():
    return DATA_SOURCES


NewTaskPayload = TaskExecutionMetaModel


@router.post("/create", status_code=201, response_model=TaskModel)
async def create_task(payload: NewTaskPayload, session: DBSessionDep):
    new_task = payload.root
    db_task = await create_new_task(new_task, session)
    return TaskModel.model_validate(db_task)


@router.get("/", response_model=Page[TaskModel])
async def get_tasks(session: DBSessionDep):
    query = (
        select(DBTask)
        .options(joinedload(DBTask.file_uploads))
        .order_by(DBTask.created_at.desc())
    )
    return await paginate(session, query)


@router.get("/{task_id}", response_model=TaskModel)
async def get_task(task_id: int, session: DBSessionDep):
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


@router.post("/{task_id}/execute", response_model=TaskModel)
async def execute_task(
    task_id: int, background_tasks: BackgroundTasks, session: DBSessionDep
):
    """
    Execute the task with the given ID.
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
async def get_task_progress(task_id: int, session: DBSessionDep):
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
async def get_task_progress_details(task_id: int, session: DBSessionDep):
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
async def download_task_logs(task_id: int, session: DBSessionDep):
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_log_path = os.path.join(TASK_LOG_DIR, f"{task_id}.log")
    return download_logs(task_log_path)


@router.get("/{task_id}/queue-items/{queue_type}")
async def get_task_queue_items(
    task_id: int,
    queue_type: QueueType,
    session: DBSessionDep,
    limit: int = 10,
    cursor_id: int | None = None,
):
    """
    Get the items in the queue for a given task.

    Args:
        task_id (int): The ID of the task.
        queue_type (QueueType): The type of queue to fetch items from.
        session (DBSessionDep): The database session dependency.
        limit (int, optional): The maximum number of items to fetch. Defaults to 10.
        cursor_id (int, optional): The ID to start fetching items from (cursor-based pagination!). Defaults to None.
    """
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    item_manager = create_task_queue_item_manager(task_id)
    items = item_manager.get_queue_items(queue_type, cursor_id, limit)
    return items


@router.delete("/{task_id}/queue-items/{queue_type}")
async def delete_task_queue_items(
    task_id: int,
    queue_type: QueueType,
    item_ids: list[int],
    session: DBSessionDep,
):
    """
    Delete items from the given type of queue for a given task.
    """
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    item_manager = create_task_queue_item_manager(task_id)

    removed_count = item_manager.remove_queue_items(item_ids, queue_type)

    return {
        "removed_count": removed_count,
        "message": f"{removed_count} items removed from {queue_type} queue for task {task_id}",
    }


@router.post("/{task_id}/queue-items/inputs")
async def add_task_inputs(
    task_id: int,
    raw_inputs: list[JSONValue],
    session: DBSessionDep,
):
    """
    Add items to the input queue for a given task.
    """
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        validated_inputs = parse_task_inputs(
            raw_inputs, data_source=task.data_source, task_type=task.task_type
        )

        item_manager = create_task_queue_item_manager(task_id)

        await item_manager.add_inputs(validated_inputs)

        if len(validated_inputs) == 0:
            raise HTTPException(status_code=400, detail="No valid inputs provided")

        return {
            "added_count": len(validated_inputs),
            "message": f"{len(validated_inputs)} items added to input queue for task {task_id}",
        }
    except InvalidTaskInputsError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "code": e.code,
                "invalid_inputs": e.invalid_inputs,
            },
        )
