import logging
import sys
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.api.routers.spotify_api import router as spotify_api_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.about import router as about_router
from app.config import PUBLIC_IP, settings
from app.db import sessionmanager

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.log_level == "DEBUG" else logging.INFO,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    print(f"Running on public IP {PUBLIC_IP}")
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/api/docs")


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Routers
app.include_router(spotify_api_router)
app.include_router(tasks_router)
app.include_router(about_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
