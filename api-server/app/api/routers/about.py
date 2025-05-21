import os
from fastapi import APIRouter
from datetime import datetime

from app.config import settings
from app.api.utils.logs import download_logs
from app.db.models import DataSource

# TODO: update whenever something major changes in the API
API_VERSION = "1.0"
ONLINE_SINCE = datetime.now().isoformat()

router = APIRouter(prefix="/about")


@router.get("/")
def about():
    return {
        "version": API_VERSION,
        "online_since": ONLINE_SINCE,
    }


@router.get("/application-logs")
async def get_application_logs():
    """
    Download application-wide logs.

    This allows debugging of issues related to the application (e.g. when what requests were made, details about exceptions etc.)
    """
    log_file_path = os.path.join(settings.app_log_dir, "app.log")
    return download_logs(log_file_path)


@router.get("/client-logs/{data_source}")
def get_api_client_logs(data_source: DataSource):
    """
    Download logs from the global API client for the given data source.

    This allows debugging of issues related to API calls for the data source (e.g. inspecting when what requests were made, when endpoints were blocked etc.)
    """
    log_file_path = os.path.join(settings.api_client_log_dir, f"{data_source}.log")
    return download_logs(log_file_path)
