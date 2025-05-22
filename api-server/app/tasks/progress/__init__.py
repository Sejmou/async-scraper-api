from typing import Sequence
from sqlalchemy import func, select
import json

from app.db import DatabaseSessionManager
from app.db.models import JSONValue
from app.tasks.progress.db_models import (
    UniqueQueueInputs,
    QueueSuccesses,
    QueueFailures,
    QueueInputsWithoutOutput,
)
from app.tasks.progress.public_models import TaskProgressModel


def bytes_to_json(data: bytes) -> JSONValue:
    return json.loads(data.decode("utf-8"))


def bytes_seq_to_json(data: Sequence[bytes]) -> list[JSONValue]:
    return [json.loads(d.decode("utf-8")) for d in data]


class TaskProgressTracker:
    def __init__(self, task_progress_db_dir: str, task_id: int):
        self._session_manager = DatabaseSessionManager(
            f"sqlite+aiosqlite:///{task_progress_db_dir}/{task_id}.db"
        )

    async def get_progress(self) -> TaskProgressModel:
        async with self._session_manager.session() as session:
            success_count = (
                await session.execute(select(func.count(QueueSuccesses._id)))
            ).scalar_one()
            failure_count = (
                await session.execute(select(func.count(QueueFailures._id)))
            ).scalar_one()
            inputs_without_output_count = (
                await session.execute(select(func.count(QueueInputsWithoutOutput._id)))
            ).scalar_one()
            remaining_count = (
                await session.execute(select(func.count(UniqueQueueInputs._id)))
            ).scalar_one()

            return TaskProgressModel(
                success_count=success_count,
                failure_count=failure_count,
                inputs_without_output_count=inputs_without_output_count,
                remaining_count=remaining_count,
            )
