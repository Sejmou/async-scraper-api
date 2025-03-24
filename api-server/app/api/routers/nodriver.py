from fastapi import APIRouter, BackgroundTasks
from app.utils.nodriver import example

router = APIRouter(prefix="/nodriver")


@router.post("/demo", status_code=202)
async def fetch_tracks(
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(example)
    return {"message": "Task added to background tasks"}
