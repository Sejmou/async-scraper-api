from logging import Logger
import os
import json
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import asyncio
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import sessionmanager
from app.tasks.common import (
    TaskInput,
    TaskProgressMeta,
    SingleItemFetchFunction,
    BatchFetchFunction,
)
from app.db.models import DataFetchingTask, S3FileUpload
from app.tasks.queue_item_management import TaskQueueItemManager
from app.utils.zstd import compress_file
from app.utils.s3 import upload_file
from app.utils.files import is_file_empty


class TaskProcessor[T: TaskInput](ABC):
    """
    A utility class for processing data fetching tasks in a queue-based manner.

    Output data is written to a JSONL file in the `TASK_OUTPUT_DIR` directory. Once the file reaches a certain size, it is compressed using zstd and uploaded to S3.
    """

    def __init__(
        self,
        server_ip: str,
        task_id: int,
        outputs_dir: str,
        queue_item_manager: TaskQueueItemManager,
        logger: Logger,
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        self._server_ip = server_ip
        """
        The IP address of the server that the task processor is running on. This is used to create unique S3 keys for the uploaded output files (making it easier to understand where uploaded files came from, e.g. if there are multiple remote servers uploading to the same S3 prefix).
        """

        self._task_id = task_id
        """
        The ID of the task that is being processed by this task processor.
        """

        self._queue_item_manager = queue_item_manager
        """
        An instance of the class that abstracts away managing the queues for the input items of the task.
        """

        self._logger = logger
        """
        The logger instance that is used to log messages about this task processor's progress.
        """

        self._logging_interval = 60
        """
        The interval (in seconds) at which the task processor logs its progress.
        """

        self._output_fp = f"{outputs_dir}/{task_id}.jsonl"
        """
        The path to the JSONL file where the outputs of the task will be written to.
        """

        self._output_fp_compressed = f"{outputs_dir}/{task_id}.jsonl.zst"
        """
        The path to the compressed JSONL file that will be uploaded to S3 once the task finishes or the current output file reaches a certain size.
        """

        self._output_file = open(self._output_fp, "a")

        self._compression_file_size_limit_bytes = compression_file_size_limit_bytes
        """
        The maximum size (in bytes) the output file may reach before it is compressed using zstd and uploaded to S3.
        After successful upload of the compressed file, a new output file is created and written to.
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
        self._queue_item_manager.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when exiting the context created via `with` statement. Applies cleanup to avoid memory leaks.
        """
        self.close()

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def progress(self) -> TaskProgressMeta:
        return self._create_progress_meta()

    def _create_progress_meta(self) -> TaskProgressMeta:
        return {
            "successes": self._queue_item_manager.success_count,
            "failures": self._queue_item_manager.failure_count,
            "inputs_without_output": self._queue_item_manager.inputs_without_output_count,
            "remaining": self._queue_item_manager.remaining_input_count,
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

            if self._queue_item_manager.remaining_input_count == 0:
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
                    raise e

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
                raise e

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
        s3_key = f"{db_task.s3_prefix}/{last_modified.strftime('%Y-%m-%d_%H-%M-%S')}_{self._server_ip}.jsonl.zst"
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
        if isinstance(output, dict):
            output["observed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            output = {
                "data": output,
                "observed_at": datetime.now(timezone.utc).isoformat(),
            }
        self._output_file.write(json.dumps(output) + "\n")
        self._logger.debug(f"Wrote output to {self._output_fp}")

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

    def _handle_failure(self, input_item: T, error: Exception):
        self._logger.error(f"Failed to process input {input_item}", exc_info=True)

    def _handle_input_without_output(self, input_without_output: T):
        self._logger.warning(f"Not output for input {input_without_output}")


class SequentialTaskProcessor[T: TaskInput](TaskProcessor[T]):
    def __init__(
        self,
        server_ip: str,
        task_id: int,
        outputs_dir: str,
        queue_item_manager: TaskQueueItemManager,
        logger: Logger,
        fetch_fn: SingleItemFetchFunction[T],
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            server_ip=server_ip,
            task_id=task_id,
            outputs_dir=outputs_dir,
            queue_item_manager=queue_item_manager,
            logger=logger,
            compression_file_size_limit_bytes=compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn

    async def _process_inputs(self, db_session: AsyncDBSession):
        async def handle_success(input_item: T, output: Any):
            await self._handle_success(db_session, input_item, output)

        async def handle_failure(input_item: T, error: Exception):
            self._handle_failure(input_item, error)

        async def handle_input_without_output(input_item: T):
            self._handle_input_without_output(input_item)

        while self._queue_item_manager.remaining_input_count > 0:
            self._log_if_it_is_time()
            if self._pause_requested:
                await self._persist_paused_state(db_session)
                self._logger.info("Paused")
                return

            await self._queue_item_manager.process_next_input_item(
                processing_fn=self._fetch_fn,
                on_success=handle_success,
                on_no_data_returned=handle_input_without_output,
                on_non_fatal_error=handle_failure,
            )


class BatchTaskProcessor[T: TaskInput](TaskProcessor[T]):
    def __init__(
        self,
        server_ip: str,
        task_id: int,
        outputs_dir: str,
        queue_item_manager: TaskQueueItemManager,
        logger: Logger,
        fetch_fn: BatchFetchFunction[T],
        batch_size: int,
        compression_file_size_limit_bytes: int = (
            500 * 1024 * 1024
        ),  # assuming 3:1 compression ratio, this should result in 500 MB files
    ):
        super().__init__(
            server_ip=server_ip,
            task_id=task_id,
            outputs_dir=outputs_dir,
            queue_item_manager=queue_item_manager,
            logger=logger,
            compression_file_size_limit_bytes=compression_file_size_limit_bytes,
        )
        self._fetch_fn = fetch_fn
        self._batch_size = batch_size

    async def _process_inputs(self, db_session: AsyncDBSession):
        async def handle_success(input_item: T, output: Any):
            await self._handle_success(db_session, input_item, output)

        async def handle_failure(input_item: T, error: Exception):
            self._handle_failure(input_item, error)

        async def handle_input_without_output(input_item: T):
            self._handle_input_without_output(input_item)

        while self._queue_item_manager.remaining_input_count > 0:
            self._log_if_it_is_time()
            if self._pause_requested:
                await self._persist_paused_state(db_session)
                self._logger.info("Paused")
                return

            await self._queue_item_manager.process_next_input_item_chunk(
                processing_fn=self._fetch_fn,
                on_success=handle_success,
                on_no_data_returned=handle_input_without_output,
                on_non_fatal_error=handle_failure,
                chunk_size=self._batch_size,
            )
