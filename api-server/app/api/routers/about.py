from fastapi import APIRouter
from datetime import datetime

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
