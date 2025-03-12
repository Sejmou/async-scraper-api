import os
import json
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import asyncio
from typing import Any, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import persistqueue
from persistqueue.serializers import json as json_serializer

from app.db import sessionmanager
from app.tasks.fetch_functions import SingleItemFetchFunction, BatchFetchFunction
from app.db.models import DataFetchingTask, S3FileUpload, JSONValue
from app.config import (
    PUBLIC_IP,
    TASK_LOG_DIR,
    TASK_OUTPUT_DIR,
    TASK_PROGRESS_DB_DIR,
    setup_logger,
)
from app.utils.zstd import compress_file
from app.utils.s3 import upload_file
from app.utils.files import is_file_empty


class TaskProcessingError(Exception):
    def __init__(self, message: str, task_id: int) -> None:
        super().__init__(message)
        self.task_id = task_id


class TaskProgressMeta(TypedDict):
    """
    A simple dictionary for storing metadata about the progress of a task. Used only to determine if a task update should be reported (not necessarily up-to-date with actual progress)
    """

    successes: int
    failures: int
    inputs_without_output: int
    remaining: int
    current_output_file_size_bytes: int


class TaskProcessor[T: JSONValue](ABC):
    """
    A utility class for processing data fetching tasks in a queue-based manner.

    The task processor is designed to be used in a context manager (i.e. with a `with` statement).

    Output data is written to a JSONL file in the `TASK_OUTPUT_DIR` directory. Once the file reaches a certain size, it is compressed using zstd and uploaded to S3.
    """

    def __init__(
        self,
        task_id: int,
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        self._task_id = task_id
        """
        The ID of the task that is being processed by this task processor.
        """

        self._logger = setup_logger(
            f"{task_id}", file_dir=TASK_LOG_DIR, log_to_console=False
        )

        self._logging_interval = 60
        """
        The interval (in seconds) at which the task processor logs its progress.
        """

        self._output_fp = f"{TASK_OUTPUT_DIR}/{task_id}.jsonl"
        """
        The path to the JSONL file where the outputs of the task will be written to.
        """

        self._output_fp_compressed = f"{TASK_OUTPUT_DIR}/{task_id}.jsonl.zst"
        """
        The path to the compressed JSONL file that will be uploaded to S3 once the task finishes or the current output file reaches a certain size.
        """

        self._output_file = open(self._output_fp, "a")

        self._compression_file_size_limit_bytes = compression_file_size_limit_bytes
        """
        The maximum size (in bytes) the output file may reach before it is compressed using zstd and uploaded to S3.
        After successful upload of the compressed file, a new output file is created and written to.
        """

        self._successes_q = persistqueue.SQLiteQueue(
            path=TASK_PROGRESS_DB_DIR,
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

        self._pause_requested = False
        """
        A flag that is set whenever the pause() method is called. Action should be taken as soon as safely possible to pause the task.
        Once it is paused, the task's status should be updated in the DB accordingly.
        """

        self._last_logged_at = datetime.now()
        """
        The timestamp of the last time the task processor logged its progress.
        """

        self._last_progress_meta: TaskProgressMeta = self._create_progress_meta()
        """
        The metadata about the progress of the task at the last time it was logged.
        """

    def __enter__(self):
        """
        Called when entering a context (at the start of a `with` statement using an instance of this class).
        """
        return self

    def close(self):
        self._output_file.close()
        self._input_q.close()
        self._failure_q.close()
        self._in_without_out_q.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting the context created via `with` statement. Applies cleanup to avoid memory leaks.
        """
        self.close()

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def remaining_inputs(self) -> list[T]:
        """
        The input items that have not been processed yet.
        """
        return self._input_q.queue()

    @property
    def remaining_count(self) -> int:
        return self._input_q.size

    @property
    def successes(self) -> list[T]:
        """
        The input items that have been processed successfully.
        """
        return self._successes_q.queue()

    @property
    def success_count(self) -> int:
        """
        The number of items that have been processed successfully (i.e. number of items for which output has been written to the output file).
        """
        return self._successes_q.size

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

    @property
    def progress(self) -> TaskProgressMeta:
        return self._create_progress_meta()

    def _create_progress_meta(self) -> TaskProgressMeta:
        return {
            "successes": self.success_count,
            "failures": self.failure_count,
            "inputs_without_output": self.inputs_without_output_count,
            "remaining": self.remaining_count,
            "current_output_file_size_bytes": os.path.getsize(self._output_fp),
        }

    def log_progress(self):
        meta = self._create_progress_meta()
        self._logger.info(f"Current task progress: {json.dumps(meta)}")
        self._last_logged_at = datetime.now()

    def _log_if_it_is_time(self):
        if (
            datetime.now() - self._last_logged_at
        ).total_seconds() >= self._logging_interval:
            new_meta = self._create_progress_meta()
            if new_meta != self._last_progress_meta:
                self.log_progress()

    async def run(self):
        async with sessionmanager.session() as db_session:
            db_task = await db_session.scalar(
                select(DataFetchingTask).where(DataFetchingTask.id == self._task_id)
                # in async SQLAlchemy we need to eagerly load any relationships as well (see also: https://github.com/sqlalchemy/sqlalchemy/discussions/8848#discussioncomment-4188599 and https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession )
                .options(joinedload(DataFetchingTask.file_uploads))
            )
            if db_task is None:
                raise ValueError(f"Task with ID {self._task_id} does not exist!")
            if db_task.status == "running":
                raise ValueError(f"Task with ID {db_task.id} is already running!")

            if self.remaining_count == 0:
                try:
                    self._logger.info("No inputs to process. Task is already done.")
                    db_task.status = "done"
                    await db_session.commit()
                    if os.path.exists(self._output_fp_compressed):
                        self._logger.info(
                            f"Uploading leftover compressed output file {self._output_fp_compressed}"
                        )
                        await self._upload_compressed_output_file_delete_local(
                            db_session
                        )
                    if os.path.exists(self._output_fp):
                        if is_file_empty(self._output_fp):
                            self._logger.info(
                                f"Output file {self._output_fp} is empty. Deleting..."
                            )
                            os.remove(self._output_fp)
                        else:
                            self._logger.info(
                                f"Output file {self._output_fp} is not empty. Compressing and uploading..."
                            )
                            await self._compress_upload_and_delete_data_written_to_current_output_file(
                                db_session
                            )
                    return

                except Exception as e:
                    db_task.status = "error"
                    await db_session.commit()
                    self._logger.exception(e)
                    raise TaskProcessingError(str(e), task_id=self._task_id)

            db_task.status = "running"
            await db_session.commit()
            self.log_progress()

            try:
                self._logger.info(f"Processing remaining inputs")
                await self._process_inputs(db_session)
                await self._compress_upload_and_delete_data_written_to_current_output_file(
                    db_session
                )
                db_task.status = "done"
                await db_session.commit()
                self._logger.info("Task completed successfully :)")
            except Exception as e:
                db_task.status = "error"
                await db_session.commit()
                self._logger.exception(e)
                raise TaskProcessingError(str(e), task_id=self._task_id)

    def pause(self):
        self._pause_requested = True
        self._logger.info("Pause requested")

    async def _persist_paused_state(self, db_session: AsyncDBSession):
        db_task = await db_session.get(DataFetchingTask, self._task_id)
        if db_task is None:
            raise ValueError(
                f"Could not pause task: No task with ID {self._task_id} exists!"
            )
        db_task.status = "paused"
        await db_session.commit()
        self._logger.debug("Persisted paused state")

    @abstractmethod
    async def _process_inputs(self, db_session: AsyncDBSession):
        """
        Processes the input items that have previously been added via add_inputs. Runs indefinitely until all input items have been processed.

        This method should be overridden by subclasses to define the processing logic.
        """
        pass

    async def _compress_upload_and_delete_data_written_to_current_output_file(
        self, db_session: AsyncDBSession
    ):
        await self._compress_output_file_delete_uncompressed()
        await self._upload_compressed_output_file_delete_local(db_session)

    async def _compress_output_file_delete_uncompressed(self):
        await asyncio.to_thread(
            compress_file,
            input_file_path=self._output_fp,
            output_file_path=self._output_fp_compressed,
            remove_input_file=True,
        )
        self._logger.info(f"Compressed output file to {self._output_fp_compressed}")

    async def _upload_compressed_output_file_delete_local(
        self, db_session: AsyncDBSession
    ):
        db_task = await db_session.get(DataFetchingTask, self._task_id)
        if db_task is None:
            raise ValueError(
                f"Could not upload compressed output file for task: No task with ID {self._task_id} exists!"
            )
        last_modified = datetime.fromtimestamp(
            os.path.getmtime(self._output_fp_compressed), tz=timezone.utc
        )
        s3_key = f"{db_task.s3_prefix}/{last_modified.strftime('%Y-%m-%d_%H-%M-%S')}_{PUBLIC_IP}.jsonl.zst"
        upload_size_bytes = os.path.getsize(self._output_fp_compressed)
        upload_meta = await upload_file(
            local_path=self._output_fp_compressed,
            s3_key=s3_key,
            remove_after_upload=True,
        )
        s3_bucket = upload_meta.s3_bucket
        s3_endpoint_url = upload_meta.s3_endpoint_url
        s3_key = upload_meta.s3_key
        db_task.file_uploads.append(
            S3FileUpload(
                s3_key=s3_key,
                s3_bucket=s3_bucket,
                s3_endpoint_url=s3_endpoint_url,
                size_bytes=upload_size_bytes,
            )
        )
        await db_session.commit()
        self._logger.info(
            f"Uploaded compressed output file to S3. endpoint: {s3_endpoint_url}, bucket: {s3_bucket}, key: {s3_key})"
        )

    async def _write_output(self, output: Any, db_session: AsyncDBSession):
        try:
            self._output_file.write(json.dumps(output) + "\n")
            self._logger.debug(f"Wrote output to {self._output_fp}")
        except Exception as e:
            self._handle_failure(output)
            raise e

        if (
            os.path.getsize(self._output_file.name)
            >= self._compression_file_size_limit_bytes
        ):
            self._output_file.close()
            await self._compress_output_file_delete_uncompressed()
            await self._upload_compressed_output_file_delete_local(db_session)
            await db_session.commit()

            self._output_file = open(self._output_fp, "a")
            self._logger.info("Rotated output file")

    async def _handle_success(self, db_session: AsyncDBSession, input_item: T, output):
        await self._write_output(output, db_session)
        self._successes_q.put(input_item)

    def _handle_failure(self, input_item: T):
        self._failure_q.put(input_item)

    def _handle_input_without_output(self, input_without_output: T):
        self._in_without_out_q.put(input_without_output)


class SequentialTaskProcessor[T: JSONValue](TaskProcessor[T]):
    def __init__(
        self,
        task_id: int,
        fetch_fn: SingleItemFetchFunction[T],
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            task_id,
            compression_file_size_limit_bytes=compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn

    async def _process_inputs(self, db_session: AsyncDBSession):
        while self.remaining_count > 0:
            self._log_if_it_is_time()
            if self._pause_requested:
                await self._persist_paused_state(db_session)
                self._logger.info("Paused")
                return

            input_item = self._input_q.get()
            item_processed = False  # use this to make sure task_done() is only called if the input_item was actually processed
            try:
                output = await self._fetch_fn(input_item)
                if output:
                    await self._handle_success(db_session, input_item, output)
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
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            task_id,
            compression_file_size_limit_bytes=compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn
        self._batch_size = batch_size

    async def _process_inputs(self, db_session: AsyncDBSession):
        while self.remaining_count > 0:
            self._log_if_it_is_time()
            if self._pause_requested:
                await self._persist_paused_state(db_session)
                return

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
                            await self._handle_success(db_session, input_item, output)
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
