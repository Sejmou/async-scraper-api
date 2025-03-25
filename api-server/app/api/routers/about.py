from fastapi import APIRouter

# TODO: update whenever something major changes in the API
API_VERSION = "0.5"

router = APIRouter(prefix="/about")


@router.get("/")
def about():
    return {
        "version": API_VERSION,
    }
