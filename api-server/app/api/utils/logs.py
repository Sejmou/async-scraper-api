import os
from fastapi import HTTPException
from fastapi.responses import FileResponse


def download_logs(log_file_path: str):
    """
    Fetch logs from the given log file path and return them as a file response.
    """
    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        log_file_path,
        media_type="text/plain",
        filename=os.path.basename(log_file_path),
    )
