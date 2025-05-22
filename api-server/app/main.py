from contextlib import asynccontextmanager
from typing import Any
from fastapi.responses import JSONResponse
import uvicorn
from fastapi import FastAPI, Request
from fastapi_pagination import add_pagination

from app.api.dependencies.core import DBSessionDep
from app.api.routers.tasks import NewTaskPayload, create_task, router as tasks_router
from app.api.routers.about import router as about_router
from app.config import PUBLIC_IP, settings, app_logger
from app.db.models import DataSource
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
add_pagination(app)


# Override the default exception handler for all unhandled exceptions.
@app.exception_handler(Exception)
async def json_exception_handler(request: Request, exc: Exception):
    app_logger.exception("Unhandled error occurred")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.post("/{data_source}/{task_type}", status_code=201)
async def legacy_create_task(
    data_source: DataSource,
    task_type: str,
    session: DBSessionDep,
    request: Request,
):
    """
    Backward-compatible endpoint that translates old task creation API requests to the new format.
    """
    old_payload: dict[str, Any] = await request.json()

    if "inputs" not in old_payload:
        return JSONResponse(
            status_code=400,
            content={"detail": "Missing 'inputs'"},
        )

    translated_payload = {
        "data_source": data_source,
        "task_type": task_type,
        "params": old_payload.get("params"),
        "inputs": old_payload["inputs"],
    }

    return await create_task(
        payload=NewTaskPayload(**translated_payload),
        session=session,
    )


# Routers
app.include_router(tasks_router)
app.include_router(about_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
