from contextlib import asynccontextmanager
import uvicorn
from fastapi import BackgroundTasks, FastAPI

from app.api.routers.spotify_api import router as spotify_api_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.about import router as about_router
from app.config import PUBLIC_IP, settings, app_logger
from app.tasks import correct_stuck_tasks_state_to_pending, resume_pending_tasks
from app.db import sessionmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    app_logger.info(f"Running on public IP {PUBLIC_IP}")
    async with sessionmanager.session() as session:
        await correct_stuck_tasks_state_to_pending(session)
        await resume_pending_tasks(session)
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/docs")


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Routers
app.include_router(spotify_api_router)
app.include_router(tasks_router)
app.include_router(about_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
