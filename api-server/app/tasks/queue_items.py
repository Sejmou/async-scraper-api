import sqlite3
from typing import Literal


type QueueType = Literal[
    "remaining_inputs", "successes", "failures", "inputs_without_output"
]

_table_names = {
    "remaining_inputs": "unique_queue_inputs",
    "successes": "queue_successes",
    "failures": "queue_failures",
    "inputs_without_output": "queue_inputs_without_output",
}


class TaskQueueItemFetcher:
    """
    A simple class to fetch items from the SQLite database storing the `persist-queue` SQLite queues for scraper task inputs (cf. processing.py)
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
        """Retrieve items from the item fetcher's SQLite database for the scraper task input queues.

        Args:
            queue_type (str): The type of queue to fetch items from. Must be one of 'remaining_inputs', 'successes', 'failures', or 'inputs_without_outputs'.
            last_id (int, optional): The ID of the last item fetched. If provided, only items with IDs greater than this will be fetched.
            limit (int, optional): The maximum number of items to fetch. Defaults to 10.

        Returns:
            list: A list of dictionaries representing the fetched items. Each dictionary contains the keys 'id', 'data', and 'added_at'. Items are ordered by their ID in ascending order (i.e. oldest come first).
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

            rows = [
                {
                    "id": row[0],
                    "data": row[1],
                    "added_at": row[2],
                }
                for row in rows
            ]

            return rows


if __name__ == "__main__":
    db_path = "/Users/sejmou/Repos/Python/scraper-api-v2/api-server/data/task_progress_dbs/72.db"
    fetcher = TaskQueueItemFetcher(db_path)
    queue_items = fetcher.get_queue_items("successes")
    print(queue_items)
