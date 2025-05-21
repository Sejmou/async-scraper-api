import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/spotify-internal")


@router.get("/logs")
async def get_logs():
    """
    Fetch logs for the Spotify internal API client.
    """
    log_file_path = os.path.join(settings.api_client_log_dir, "spotify-internal.log")
    if not os.path.exists(log_file_path):
        return HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        log_file_path,
        media_type="text/plain",
        filename="spotify-internal-api-client.log",
    )
