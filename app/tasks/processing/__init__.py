import asyncio
import os
import json
from abc import ABC, abstractmethod
from typing import Any
import persistqueue
from persistqueue.serializers import json as json_serializer

from app.db.models import DataFetchingTask, JSONValue
from app.db import sessionmanager
from app.config import settings
from app.tasks.fetch_functions import (
    SingleItemFetchFunction,
    BatchFetchFunction,
)

TASK_OUTPUT_DIR = settings.task_output_dir
TASK_PROGRESS_DB_DIR = settings.task_progress_dbs_dir


class TaskProcessor[T: JSONValue](ABC):
    """
    A utility class for processing data fetching tasks in a queue-based manner.

    The task processor is designed to be used in a context manager (i.e. with a `with` statement).

    """

    def __init__(
        self,
        task_id: int,
        compression_file_size_limit_bytes: int = 500
        * 1024
        * 1024,  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        self._task_id = task_id
        """
        The ID of the task that is being processed by this task processor.
        """

        output_fp = f"{TASK_OUTPUT_DIR}/{task_id}.jsonl"
        """
        The path to the JSONL file where the outputs of the task will be written to.
        """

        self._output_file = open(output_fp, "a")

        self._compression_file_size_limit_bytes = compression_file_size_limit_bytes
        """
        The maximum size (in bytes) the output file may reach before it is compressed using zstd and uploaded to S3.
        After successful upload of the compressed file, a new output file is created and written to.
        """

        self._success_count = 0
        """
        The number of items that have been processed successfully.
        """

        self._input_q = persistqueue.UniqueQ(
            path=TASK_PROGRESS_DB_DIR,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            # if auto_commit is False, task_done() must be called to persist changes made via put() or get() calls
            auto_commit=False,
            name="inputs",
        )
        """
        The persistent queue for input items that have not been processed yet.
        """

        self._failure_q = persistqueue.SQLiteQueue(
            path=TASK_PROGRESS_DB_DIR,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            auto_commit=True,
            name="failures",
        )
        """
        The queue for items that could not be processed due to an error.
        """

        self._in_without_out_q = persistqueue.SQLiteQueue(
            path=TASK_PROGRESS_DB_DIR,
            db_file_name=f"{task_id}.db",
            serializer=json_serializer,
            auto_commit=True,
            name="inputs_without_output",
        )
        """
        The queue for input items that haven't produced any output.
        """

    def __enter__(self):
        """
        Called when entering a context (at the start of a `with` statement using an instance of this class).
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting the context. Applies cleanup to avoid memory leaks.
        """
        self._output_file.close()
        self._input_q.close()
        self._failure_q.close()
        self._in_without_out_q.close()

    @property
    def remaining_inputs(self) -> list[T]:
        """
        Returns the input items that have not been processed yet.
        """

        items = self._input_q.queue()
        return items

    @property
    def remaining_count(self) -> int:
        return self._input_q.size

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def failures(self) -> list[T]:
        """
        Returns the input items that could not be processed due to an error.
        """
        return self._failure_q.queue()

    @property
    def failure_count(self) -> int:
        return self._failure_q.size

    @property
    def inputs_without_output(self) -> list[T]:
        """
        Returns the input items that haven't produced any output.
        """
        return self._in_without_out_q.queue()

    @property
    def inputs_without_output_count(self) -> int:
        return self._in_without_out_q.size

    def add_inputs(self, inputs: list[T]):
        for item in inputs:
            self._input_q.put(item)
        self._input_q.task_done()

    async def run(self):
        async with sessionmanager.session() as db_session:
            db_task = await db_session.get(DataFetchingTask, self._task_id)
            if db_task is None:
                raise ValueError(f"Task with ID {self._task_id} does not exist!")
            if db_task.status == "running":
                raise ValueError(f"Task with ID {db_task.id} is already running!")
            db_task.status = "running"
            await db_session.commit()

            try:
                asyncio.create_task(self._process_inputs_until_done())
                db_task.status = "done"
            except asyncio.CancelledError:
                db_task.status = "paused"
            except Exception:
                db_task.status = "error"
                await db_session.commit()

    @abstractmethod
    async def _process_inputs_until_done(self):
        """
        Processes the input items that have previously been added via add_inputs. Runs indefinitely until all input items have been processed.

        This method should be overridden by subclasses to define the processing logic.
        """
        pass

    def _write_output(self, output: Any):
        self._output_file.write(json.dumps(output) + "\n")
        self._success_count += 1

        if (
            os.path.getsize(self._output_file.name)
            >= self._compression_file_size_limit_bytes
        ):
            self._output_file.close()
            # TODO: Compress the file using zstd and upload it to S3
            self._output_file = open(self._output_file.name, "a")

    def _handle_failure(self, input_item: T):
        self._failure_q.put(input_item)

    def _handle_input_without_output(self, input_without_output: T):
        self._in_without_out_q.put(input_without_output)


class SequentialTaskProcessor[T: JSONValue](TaskProcessor[T]):
    def __init__(
        self,
        task_id: int,
        fetch_fn: SingleItemFetchFunction[T],
        compression_file_size_limit_bytes: int = 500
        * 1024
        * 1024,  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            task_id,
            compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn

    async def _process_inputs_until_done(self):
        while self.remaining_count > 0:
            input_item = self._input_q.get()
            item_processed = False  # use this to make sure task_done() is only called if the input_item was actually processed
            try:
                output = await self._fetch_fn(input_item)
                if output:
                    self._write_output(output)
                    item_processed = True
                else:
                    self._handle_input_without_output(input_item)
                    item_processed = True
            except Exception as e:
                self._handle_failure(input_item)
                item_processed = True
                raise e
            finally:
                if item_processed:
                    # 'commit changes' to the queue so that they are persisted even if the server crashes immediately after processing the input item
                    self._input_q.task_done()


class BatchTaskProcessor[T: JSONValue](TaskProcessor[T]):
    def __init__(
        self,
        task_id: int,
        fetch_fn: BatchFetchFunction[T],
        batch_size: int,
        compression_file_size_limit_bytes: int = 500
        * 1024
        * 1024,  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            task_id,
            compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn
        self._batch_size = batch_size

    async def _process_inputs_until_done(self):
        while self.remaining_count > 0:
            batch: list[T] = []
            for _ in range(self._batch_size):
                if self.remaining_count == 0:
                    break
                batch.append(self._input_q.get())
            batch_processed = False  # use this to make sure task_done() is only called if the batch was actually processed
            try:
                outputs = await self._fetch_fn(batch)
                if outputs:
                    if len(outputs) != len(batch):
                        raise ValueError(
                            f"Expected {len(batch)} outputs, but got {len(outputs)} instead!"
                        )
                    for input_item, output in zip(batch, outputs):
                        if output:
                            self._write_output(output)
                        else:
                            self._handle_input_without_output(input_item)
                    batch_processed = True
                else:
                    for input_item in batch:
                        self._handle_input_without_output(input_item)
                    batch_processed = True
            except Exception as e:
                for input_item in batch:
                    self._handle_failure(input_item)
                batch_processed = True
                raise e
            finally:
                if batch_processed:
                    # 'commit changes' to the queue so that they are persisted even if the server crashes immediately after processing the batch
                    self._input_q.task_done()
