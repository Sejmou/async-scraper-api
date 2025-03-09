from fastapi import APIRouter

from sqlalchemy import select
from app.api.dependencies.core import DBSessionDep
from app.db.models import DataFetchingTask

router = APIRouter(prefix="/tasks")


@router.get("/")
async def tasks(session: DBSessionDep):
    tasks = await session.scalars(select(DataFetchingTask))
    return tasks
