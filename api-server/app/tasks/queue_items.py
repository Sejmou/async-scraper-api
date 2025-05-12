import sqlite3
from typing import Literal

from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from app.db.models import JSONValue
from app.tasks import get_task_processor_by_id


type QueueType = Literal[
    "remaining-inputs", "successes", "failures", "inputs-without-output"
]

_table_names: dict[QueueType, str] = {
    "remaining-inputs": "unique_queue_inputs",
    "successes": "queue_successes",
    "failures": "queue_failures",
    "inputs-without-output": "queue_inputs_without_output",
}
"""
A dictionary mapping queue types to their corresponding SQLite table names.
"""


class InvalidQueueInputsError(Exception):
    """
    Exception raised when the input items for a queue do not match the expected schema.
    """

    def __init__(self, error_msgs: list[str]):
        self.errors = error_msgs
        super().__init__(
            f"Encountered {len(error_msgs)} queue input{'s' if len(error_msgs) > 1 else ''}:\n{'\n'.join([' - ' + line for line in error_msgs])}"
        )


class TaskQueueItemManager:
    """
    A class to manage items in the `persist-queue` SQLite queues for scraper task inputs (created by the TaskProcessor for a particular task, cf. processing.py)
    """

    def __init__(
        self,
        task_id: int,
        db_path: str,
        input_item_cls: type[str] | type[int] | type[BaseModel],
    ):
        """
        Args:
            task_id (int): The ID of the task for which the queue items are being managed.
            db_path (str): The path to the SQLite database file which stores the `persist-queue` SQLite queues for scraper task inputs.
            input_item_cls (type[str] | type[int] | type[BaseModel]): The Pydantic model class (or "wrapper class" for integers or strings in case of integers or strings (usually IDs) as inputs) used to validate the items in the queue. It is used for validating the items before adding them to the queue.
        """
        self.db_path = db_path
        """
        The path to the SQLite database file which stores the `persist-queue` SQLite queues for scraper task inputs.
        """

        self.task_id = task_id
        """
        The ID of the task for which the queue items are being managed.
        """

        self._validate_queue_item = TypeAdapter(input_item_cls).validate_python
        """
        A function that validates any input (making sure it is an instance of `input_item_cls`), derived from the validate_python function of an instance of TypeAdapter created for the given `input_item_cls`.
        """

    def get_queue_items(
        self,
        queue_type: QueueType,
        cursor_id: int | None = None,
        limit: int = 10,
    ):
        """Retrieve items from the item fetcher's SQLite database for the scraper task input queues using cursor-based pagination (i.e. a cursor ID is used to fetch the next set of items).
        This method fetches items from the specified queue type, starting from the given cursor ID (if provided) and limiting the number of items returned to the specified limit.

        The items are ordered by their ID in ascending order (i.e. oldest come first).

        Args:
            queue_type (QueueType): The type of queue to fetch items from.
            cursor_id (int, optional): The ID
            limit (int, optional): The maximum number of items to fetch. Defaults to 10.

        Returns:
            dict: A dictionary containing the fetched items and the ID of the next item in the queue (after the last item returned in "items").
                - "items": A list of dictionaries representing the fetched items. Each dictionary contains the keys 'id', 'data', and 'added_at'. Items are ordered by their ID in ascending order (i.e. oldest come first).
                - "next_cursor": The ID of the next item in the queue (after the last item returned in "items"), or None if there are no more items.
                - "total": The total number of items in the queue.
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                  _id AS id,
                  CAST(data AS text) AS data,
                  datetime(timestamp, 'unixepoch') AS added_at
                FROM {_table_names[queue_type]}
                {'WHERE _id >= ?' if cursor_id else ''} ORDER BY id ASC LIMIT ?
                """,
                (cursor_id, limit) if cursor_id else (limit,),
            )
            rows = cursor.fetchall()

            items = [
                {
                    "id": row[0],
                    "data": row[1],
                    "added_at": row[2],
                }
                for row in rows
            ]

            last_id = items[-1]["id"] if items else None
            if last_id:
                next_id_tuple = cursor.execute(
                    f"SELECT _id AS id FROM {_table_names[queue_type]} WHERE _id > ? ORDER BY id ASC LIMIT 1",
                    (last_id,),
                ).fetchone()
                if next_id_tuple:
                    next_id = next_id_tuple[0]
                else:
                    next_id = None
            else:
                next_id = None

            total = cursor.execute(
                f"SELECT COUNT(*) FROM {_table_names[queue_type]}",
            ).fetchone()[0]

            return {"items": items, "next_cursor": next_id, "total": total}

    def remove_queue_item(self, id: int, queue_type: QueueType):
        """Remove an item from the queue.

        Args:
            id (int): The ID of the item to remove.
            queue_type (QueueType): The type of queue to remove the item from.

        Returns:
            bool: True if the item was successfully removed, False otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {_table_names[queue_type]} WHERE _id = ?",
                (id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    async def add_inputs(
        self,
        raw_items: list[JSONValue],
        db_session: AsyncDBSession,
    ):
        """Add new inputs to the given task. The items are validated
        (i.e. an error is raised if they don't match the expected schema for queue inputs for the given task).

        Args:
            items (list[JSONValue]): The items to add to the queue.
            queue_type (QueueType): The type of queue to add the items to.

        """

        error_msgs: list[str] = []
        validated_items: list[BaseModel | str | int] = []
        for i, raw_item in enumerate(raw_items):
            try:
                validated = self._validate_queue_item(raw_item)
                validated_items.append(validated)
            except ValidationError as e:
                error_msgs.append(f"Index {i}: {e}")
                continue

        if error_msgs:
            raise InvalidQueueInputsError(error_msgs)

        # we need to get the task processor as it has a method to add items to the queue (kinda ugly, but easier and less likely to result in unintended side-effects than recreating `persist-queue` instances used by the task processor internally)
        # TODO: think about whether there is a cleaner solution
        task_processor = await get_task_processor_by_id(self.task_id, db_session)
        task_processor.add_inputs(validated_items)


if __name__ == "__main__":
    db_path = "/Users/sejmou/Repos/Python/scraper-api-v2/api-server/data/task_progress_dbs/72.db"
    fetcher = TaskQueueItemManager(db_path)
    queue_items = fetcher.get_queue_items("successes")
    print(queue_items)
