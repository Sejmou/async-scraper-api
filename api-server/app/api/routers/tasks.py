import asyncio
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.api.dependencies.core import DBSessionDep
from app.db.models import (
    DATA_SOURCES,
    DataFetchingTask as DBTask,
    JSONValue,
)
from app.api.models import DataFetchingTaskModel, S3FileUploadModel
from app.tasks import create_new_task, get_task_processor, run_in_background
from app.tasks.input_validation import InvalidTaskInputsError, parse_task_inputs
from app.tasks.models import TaskExecutionMetaModel, TaskInputs
from app.config import TASK_LOG_DIR, TASK_PROGRESS_DB_DIR, app_logger
from app.tasks.progress import TaskProgressTracker
from app.tasks.progress.public_models import TaskProgressModel
from app.tasks.queue_item_management import (
    QueueItemRetrievalResult,
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


def create_task_progress_tracker(task_id: int) -> TaskProgressTracker:
    """
    Create a TaskProgressTracker instance with the proper database path, inferred from settings.
    """
    return TaskProgressTracker(
        task_progress_db_dir=TASK_PROGRESS_DB_DIR, task_id=task_id
    )


def add_task_inputs_in_background(task_id: int, inputs: TaskInputs):
    q_mgr = create_task_queue_item_manager(task_id)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, q_mgr.add_inputs, inputs)


async def convert_to_public_model(db_task: DBTask) -> DataFetchingTaskModel:
    """
    Convert a database task to a public model.
    """
    model = DataFetchingTaskModel(
        id=db_task.id,
        status=db_task.status,
        data_source=db_task.data_source,
        file_uploads=[
            S3FileUploadModel.model_validate(upload) for upload in db_task.file_uploads
        ],
        task_type=db_task.task_type,
        params=db_task.params,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
    )
    return model


@router.get("/data-sources")
def get_data_sources():
    return DATA_SOURCES


NewTaskPayload = TaskExecutionMetaModel


@router.post("/create", status_code=201, response_model=DataFetchingTaskModel)
async def create_task(
    payload: NewTaskPayload, session: DBSessionDep
) -> DataFetchingTaskModel:
    new_task = payload.root
    db_task, inputs = await create_new_task(new_task, session)
    if inputs:
        add_task_inputs_in_background(db_task.id, inputs)
    return await convert_to_public_model(db_task)


@router.get("/", response_model=Page[DataFetchingTaskModel])
async def get_tasks(session: DBSessionDep) -> Page[DataFetchingTaskModel]:
    query = (
        select(DBTask)
        .options(joinedload(DBTask.file_uploads))
        .order_by(DBTask.created_at.desc())
    )
    return await paginate(session, query)


@router.get("/{task_id}", response_model=DataFetchingTaskModel)
async def get_task(task_id: int, session: DBSessionDep) -> DataFetchingTaskModel:
    db_task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await convert_to_public_model(db_task)


@router.post("/{task_id}/pause", response_model=DataFetchingTaskModel)
async def pause_task(task_id: int, session: DBSessionDep) -> DataFetchingTaskModel:
    """
    Pause a task processor with the given ID.
    """
    db_task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if db_task:
        if db_task.status == "error":
            raise HTTPException(status_code=400, detail="Task is in error state")
        if db_task.status == "done":
            raise HTTPException(status_code=400, detail="Task is already done")
        if db_task.status == "pausing":
            raise HTTPException(status_code=400, detail="Task is already pausing")
        db_task.status = "pausing"
        await session.commit()
        processor = get_task_processor(db_task)
        app_logger.info(f"Pausing processor for task ID {task_id}...")
        processor.pause()
        return await convert_to_public_model(db_task)
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/execute", response_model=DataFetchingTaskModel)
async def execute_task(
    task_id: int, background_tasks: BackgroundTasks, session: DBSessionDep
) -> DataFetchingTaskModel:
    """
    Execute the task with the given ID.
    """
    db_task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if db_task:
        if db_task.status == "done":
            raise HTTPException(status_code=400, detail="Task is already done")
        if db_task.status == "pending":
            raise HTTPException(
                status_code=400, detail="Task is already resuming (pending)"
            )
        if db_task.status == "running":
            raise HTTPException(status_code=400, detail="Task is already running")
        db_task.status = "pending"
        await session.commit()
        processor = get_task_processor(db_task)
        app_logger.info(f"Resuming processor for task ID {task_id}...")
        run_in_background(processor, background_tasks)
        return await convert_to_public_model(db_task)
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/{task_id}/progress", response_model=TaskProgressModel)
async def get_task_progress(task_id: int, session: DBSessionDep) -> TaskProgressModel:
    task = await session.scalar(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(joinedload(DBTask.file_uploads))
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    progress_tracker = create_task_progress_tracker(task_id)
    progress = await progress_tracker.get_progress()
    return progress


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


@router.get(
    "/{task_id}/queue-items/{queue_type}", response_model=QueueItemRetrievalResult
)
async def get_task_queue_items(
    task_id: int,
    queue_type: QueueType,
    session: DBSessionDep,
    limit: int = 10,
    cursor_id: int | None = None,
) -> QueueItemRetrievalResult:
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

        if len(validated_inputs) == 0:
            raise HTTPException(status_code=400, detail="No valid inputs provided")

        add_task_inputs_in_background(task_id, validated_inputs)

        return {
            "received_count": len(validated_inputs),
            "message": f"{len(validated_inputs)} items will be added to input queue (assuming they are not already in the queue)",
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
