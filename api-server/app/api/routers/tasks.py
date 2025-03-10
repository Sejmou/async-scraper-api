from fastapi import APIRouter

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.api.dependencies.core import DBSessionDep
from app.db.models import DataFetchingTask as DBTask
from app.api.models import DataFetchingTask as TaskModel

router = APIRouter(prefix="/tasks")


@router.get("/", response_model=list[TaskModel])
async def tasks(session: DBSessionDep):
    tasks = (
        await session.scalars(
            # in async SQLAlchemy we need to eagerly load any relationships as well (see also: https://github.com/sqlalchemy/sqlalchemy/discussions/8848#discussioncomment-4188599 and https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession )
            select(DBTask).options(joinedload(DBTask.file_uploads))
        )
    ).unique()
    return [TaskModel.model_validate(task) for task in tasks]
