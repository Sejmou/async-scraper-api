import sqlite3
from typing import Literal


type QueueType = Literal[
    "remaining_inputs", "successes", "failures", "inputs_without_output"
]

_table_names: dict[QueueType, str] = {
    "remaining_inputs": "unique_queue_inputs",
    "successes": "queue_successes",
    "failures": "queue_failures",
    "inputs_without_output": "queue_inputs_without_output",
}
"""
A dictionary mapping queue types to their corresponding SQLite table names.
"""


class TaskQueueItemManager:
    """
    A simple class to manage items in the `persist-queue` SQLite queues for scraper task inputs (created by the TaskProcessor for a particular task, cf. processing.py)
    """

    def __init__(self, db_path):
        """
        Args:
            db_path (str): The path to the SQLite database file which stores the `persist-queue` SQLite queues for scraper task inputs.
        """
        self.db_path = db_path

    def get_queue_items(
        self,
        queue_type: QueueType,
        last_id: int | None = None,
        limit: int = 10,
    ):
        """Retrieve items from the item fetcher's SQLite database for the scraper task input queues using cursor-based pagination (i.e. the last ID of the previous page is used to fetch the next page).

        Args:
            queue_type (str): The type of queue to fetch items from. Must be one of 'remaining_inputs', 'successes', 'failures', or 'inputs_without_outputs'.
            last_id (int, optional): The ID of the last item fetched. If provided, only items with IDs greater than this will be fetched.
            limit (int, optional): The maximum number of items to fetch. Defaults to 10.

        Returns:
            dict: A dictionary containing the fetched items and the ID of the next item to fetch.
                - "items": A list of dictionaries representing the fetched items. Each dictionary contains the keys 'id', 'data', and 'added_at'. Items are ordered by their ID in ascending order (i.e. oldest come first).
                - "next_cursor": The ID of the next item to fetch, or None if there are no more items.
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
                {'WHERE _id > ?' if last_id else ''} ORDER BY id ASC LIMIT ?
                """,
                (last_id, limit) if last_id else (limit,),
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
            queue_type (str): The type of queue to remove the item from. Must be one of 'remaining_inputs', 'successes', 'failures', or 'inputs_without_outputs'.

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


if __name__ == "__main__":
    db_path = "/Users/sejmou/Repos/Python/scraper-api-v2/api-server/data/task_progress_dbs/72.db"
    fetcher = TaskQueueItemManager(db_path)
    queue_items = fetcher.get_queue_items("successes")
    print(queue_items)
