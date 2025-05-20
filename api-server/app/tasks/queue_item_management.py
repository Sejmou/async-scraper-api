import json
import sqlite3
from typing import Any, Awaitable, Callable, Literal, Sequence, TypedDict
import os
import persistqueue
from persistqueue.serializers import json as json_serializer

from app.tasks.common import (
    JSONValue,
    FatalProcessingError,
)


class EmptyQueueError(Exception):
    """
    Exception raised when the queue is empty and no items are available for processing.
    This exception is used to indicate that there are no items to process in the queue.
    """

    pass


class QueueItemCounts(TypedDict):
    """
    A simple dictionary, storing the current counts of items in the different queues.
    """

    successes: int
    failures: int
    inputs_without_output: int
    remaining: int


type QueueType = Literal["inputs", "successes", "failures", "inputs-without-output"]

# TODO: use a more specific type for the input item (couldn't figure it out with my smooth brain yet)
type QueueItemProcessingSuccessCallback = Callable[[Any, Any], Awaitable[None] | None]
type QueueItemProcessingNoDataReturnedCallback = Callable[[Any], Awaitable[None] | None]
type QueueItemProcessingNonFatalErrorCallback = Callable[
    [Any, Exception], Awaitable[None] | None
]

_table_names: dict[QueueType, str] = {
    "inputs": "unique_queue_inputs",
    "successes": "queue_successes",
    "failures": "queue_failures",
    "inputs-without-output": "queue_inputs_without_output",
}
"""
A dictionary mapping queue types to their corresponding SQLite table names.
"""


class QueueItemData(TypedDict):
    """
    A simple dictionary for data + metadata about a queue item.
    """

    id: int
    """
    The ID of the queue item.
    """
    data: JSONValue
    """
    The data associated with the queue item. The exact data type depends on the underlying task's `data_source` and `task_type`.
    """
    added_at: str
    """
    An ISO 8601 formatted string representing the timestamp when the queue item was added to the queue.
    """


class QueueItemRetrievalResult(TypedDict):
    """
    A simple dictionary for the result of a queue item retrieval operation.
    """

    items: list[QueueItemData]
    """
    A list of dictionaries representing the retrieved queue items.
    """
    next_cursor: int | None
    """
    The ID of the next item in the queue (after the last item returned in "items"), or None if there are no more items.
    """
    total: int
    """
    The total number of items in the queue.
    """


class TaskQueueItemManager:
    """
    A class to manage items in the `persist-queue` SQLite queues for scraper task inputs (created by the TaskProcessor for a particular task, cf. processing.py)
    """

    def __init__(
        self,
        task_id: int,
        db_dir: str,
    ):
        """
        Args:
            task_id (int): The ID of the task for which the queue items are being managed.
            db_dir (str): The directory where the SQLite database file should be stored.
        """

        self._task_id = task_id
        """
        The ID of the task for which the queue items are being managed.
        """

        self._successes_q = persistqueue.SQLiteQueue(
            path=db_dir,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            # if auto_commit is False, task_done() must be called to persist changes made via put() or get() calls
            auto_commit=False,
            name="successes",
        )
        """
        The items that have been processed successfully.
        """

        self._input_q = persistqueue.UniqueQ(
            path=db_dir,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            # if auto_commit is False, task_done() must be called to persist changes made via put() or get() calls
            auto_commit=False,
            name="inputs",
        )
        """
        The persistent queue for input items that have not been processed yet.
        """

        def undo_input_queue_removals():
            self._input_q = persistqueue.UniqueQ(
                path=db_dir,
                db_file_name=f"{task_id}.db",
                serializer=json_serializer,
                # if auto_commit is False, task_done() must be called to persist changes made via put() or get() calls
                auto_commit=False,
                name="inputs",
            )

        self._undo_input_removals = undo_input_queue_removals
        """
        A hack to reset the input queue to the state it was in before any calls to get() after the last call to task_done() (i.e. the state before persisting queue item removals made via get() calls).
        """

        self._failure_q = persistqueue.SQLiteQueue(
            path=db_dir,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            auto_commit=True,
            name="failures",
        )
        """
        The queue for items that could not be processed due to an error.
        """

        self._in_without_out_q = persistqueue.SQLiteQueue(
            path=db_dir,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            auto_commit=True,
            name="inputs_without_output",
        )
        """
        The queue for input items that haven't produced any output.
        """

        self._db_path = os.path.join(db_dir, f"{task_id}.db")
        """
        The path to the SQLite database file which stores the `persist-queue` SQLite queues for scraper task inputs.
        """

    @property
    def queue_item_counts(self) -> QueueItemCounts:
        """
        Returns the current counts of items in the different queues.
        """

        return {
            "successes": self._successes_q.size,
            "failures": self._failure_q.size,
            "inputs_without_output": self._in_without_out_q.size,
            "remaining": self._input_q.size,
        }

    def get_queue_items(
        self,
        queue_type: QueueType,
        cursor_id: int | None = None,
        limit: int = 10,
    ) -> QueueItemRetrievalResult:
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

        with sqlite3.connect(self._db_path) as conn:
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

            items: list[QueueItemData] = [
                {
                    "id": row[0],
                    "data": json.loads(row[1]),
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

    def remove_queue_items(self, ids: Sequence[int], queue_type: QueueType):
        """Remove the items associated with the given ids from the specified queue type.

        Args:
            ids: The IDs of the items to remove.
            queue_type: The type of queue to remove the items from.

        Returns:
            int: The number of items removed from the queue.
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ids)
            cursor.execute(
                f"DELETE FROM {_table_names[queue_type]} WHERE _id IN ({placeholders})",
                ids,
            )
            conn.commit()
            return cursor.rowcount

    async def process_next_input_item(
        self,
        processing_fn: Callable[[Any], Awaitable[Any]],
        on_success: QueueItemProcessingSuccessCallback,
        on_no_data_returned: QueueItemProcessingNoDataReturnedCallback,
        on_non_fatal_error: QueueItemProcessingNonFatalErrorCallback,
    ) -> None:
        """
        Processes the next input item from the queue using the provided processing function.

        The (async!) processing function should return an output corresponding to the input item.
        If the processing function completes successfully, the output is checked:
        - If the output is not None, the input item is added to the "successes" queue and the `on_success` callback function is called with the input item and its corresponding output.
        - If the output is None, the input item is added to the "inputs-without-output" queue and the `on_no_data_returned` callback function is called.

        If the processing function raises a FatalProcessingError, it is re-raised so that it can be handled appropriately by the caller and any related ongoing processes can exit cleanly.
        If the processing function raises any other exception, the input item is added to the failures queue and the provided `on_non_fatal_error` callback function is called.

        Args:
            processing_fn: The processing function to apply to the input item.
            on_success: Callback function to call when the processing function completes successfully.
            on_no_data_returned: Callback function to call when the processing function returns None.
            on_non_fatal_error: Callback function to call when a non-fatal error occurs during processing.

        Raises:
            FatalProcessingError: If a fatal error occurs during processing.
            EmptyQueueError: If the input queue is empty and no items are available for processing.
        """
        if self._input_q.empty():
            raise EmptyQueueError(
                "No items in the input queue. Cannot process next item."
            )
        item = self._input_q.get()

        try:
            res = await processing_fn(item)
            if res is None:
                on_no_data_returned(item)
                self._in_without_out_q.put(item)
            else:
                on_success(item, res)
                self._successes_q.put(item)
        except FatalProcessingError:
            self._undo_input_removals()
            raise
        except Exception as e:
            # every exception that is not a FatalProcessingError is considered a non-fatal error
            on_non_fatal_error(item, e)
            self._failure_q.put(item)
        finally:
            # persist the removal from the input queue
            self._input_q.task_done()

    async def process_next_input_item_chunk(
        self,
        processing_fn: Callable[[Sequence[Any]], Awaitable[Sequence[Any]]],
        on_success: QueueItemProcessingSuccessCallback,
        on_no_data_returned: QueueItemProcessingNoDataReturnedCallback,
        on_non_fatal_error: QueueItemProcessingNonFatalErrorCallback,
        chunk_size: int,
    ):
        """
        Processes the next chunk of input items from the queue using the provided processing function.

        The (async!) processing function should return outputs for the given input items (exactly one output for each input item).

        If the processing function completes successfully, the length of the outputs is first checked against the length of the inputs (if they do not match, a FatalProcessingError is raised).
        Then, each output is checked:
        - If the output is not None, the input item is added to the "successes" queue and the `on_success` callback function is called with the input item and its corresponding output.
        - If the output is None, the input item is added to the "inputs-without-output" queue and the `on_no_data_returned` callback function is called.

        If the processing function raises a FatalProcessingError, it is re-raised so that it can be handled appropriately by the caller and any related ongoing processes can exit cleanly.
        If the processing function raises any other exception, each input item is added to the failures queue and the provided `on_non_fatal_error` callback function is called.

        Args:
            processing_fn: The processing function to apply to the input items.
            on_success: Callback function to call when the processing function completes successfully.
            on_no_data_returned: Callback function to call when the processing function returns None.
            on_non_fatal_error: Callback function to call when a non-fatal error occurs during processing.
            chunk_size: The number of items to process in a single chunk. Must be greater than 1.
            If the chunk size is less than 2, a ValueError is raised.

        Raises:
            FatalProcessingError: If a fatal error occurs during processing.
            EmptyQueueError: If the input queue is empty and no items are available for processing.
            ValueError: If the chunk size is less than 2.
        """
        if chunk_size < 2:
            raise ValueError("Chunk size must be greater than 1.")
        inputs: list = []
        while not self._input_q.empty() and len(inputs) < chunk_size:
            item = self._input_q.get()
            inputs.append(item)
        if not inputs:
            raise EmptyQueueError(
                "No items in the input queue. Cannot process next item."
            )

        try:
            outputs = await processing_fn(inputs)
            if outputs is None:
                for item in inputs:
                    on_no_data_returned(item)
                    self._in_without_out_q.put(item)
            else:
                if len(outputs) != len(inputs):
                    raise FatalProcessingError(
                        f"Processing function returned {len(outputs)} items (expected {len(inputs)})."
                    )
                for input_item, output in zip(inputs, outputs):
                    if output is None:
                        on_no_data_returned(input_item)
                        self._in_without_out_q.put(input_item)
                    else:
                        on_success(input_item, output)
                        self._successes_q.put(input_item)
        except FatalProcessingError:
            self._undo_input_removals()
            raise
        except Exception as e:
            # every exception that is not a FatalProcessingError is considered a non-fatal error
            for input_item in inputs:
                on_non_fatal_error(input_item, e)
                self._failure_q.put(input_item)
        finally:
            # persist the removals from the input queue
            self._input_q.task_done()

    async def add_inputs(
        self,
        inputs: Sequence,
    ):
        """
        Add new inputs to the given task.
        """
        for item in inputs:
            self._input_q.put(item)

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def remaining_input_count(self) -> int:
        return self._input_q.size

    @property
    def success_count(self) -> int:
        """
        The number of items that have been processed successfully (i.e. number of items for which output has been written to the output file).
        """
        return self._successes_q.size

    @property
    def failure_count(self) -> int:
        return self._failure_q.size

    @property
    def inputs_without_output_count(self) -> int:
        return self._in_without_out_q.size

    def __enter__(self):
        """
        Called when entering a context (at the start of a `with` statement using an instance of this class).
        """
        return self

    def close(self):
        self._input_q.close()
        self._failure_q.close()
        self._in_without_out_q.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting the context created via `with` statement. Applies cleanup to avoid memory leaks.
        """
        self.close()
