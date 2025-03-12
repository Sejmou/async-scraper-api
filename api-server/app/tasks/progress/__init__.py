from typing import Sequence
from sqlalchemy import func, select
import json
from app.config import TASK_PROGRESS_DB_DIR
from app.db import DatabaseSessionManager
from app.db.models import JSONValue
from app.tasks.progress.db_models import (
    UniqueQueueInputs,
    QueueSuccesses,
    QueueFailures,
    QueueInputsWithoutOutput,
)
from app.tasks.progress.public_models import TaskProgress, TaskProgressDetails


def bytes_to_json(data: bytes) -> JSONValue:
    return json.loads(data.decode("utf-8"))


def bytes_seq_to_json(data: Sequence[bytes]) -> list[JSONValue]:
    return [json.loads(d.decode("utf-8")) for d in data]


class TaskProgressTracker[T: JSONValue]:
    def __init__(self, task_id: int):
        self._session_manager = DatabaseSessionManager(
            f"sqlite+aiosqlite:///{TASK_PROGRESS_DB_DIR}/{task_id}.db"
        )

    async def get_progress(self) -> TaskProgress:
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

            return TaskProgress(
                success_count=success_count,
                failure_count=failure_count,
                inputs_without_output_count=inputs_without_output_count,
                remaining_count=remaining_count,
            )

    async def get_progress_details(self) -> TaskProgressDetails[T]:
        async with self._session_manager.session() as session:
            successes = (
                (await session.execute(select(QueueSuccesses.data))).scalars().all()
            )
            failures = (
                (await session.execute(select(QueueFailures.data))).scalars().all()
            )
            inputs_without_output = (
                (await session.execute(select(QueueInputsWithoutOutput.data)))
                .scalars()
                .all()
            )
            remaining = (
                (await session.execute(select(UniqueQueueInputs.data))).scalars().all()
            )

            return TaskProgressDetails[T](
                successes=bytes_seq_to_json(successes),  # type: ignore
                failures=bytes_seq_to_json(failures),  # type: ignore
                inputs_without_output=bytes_seq_to_json(inputs_without_output),  # type: ignore
                remaining=bytes_seq_to_json(remaining),  # type: ignore
            )
