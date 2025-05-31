import os
from pathlib import Path
import logging
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.utils.misc import get_public_ip

file_dir = Path(__file__).parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_file_path: str = f"{file_dir.parent.resolve()}/data/app.db"
    """
    The path where the SQLite database for the application's core data (excluding task progress state) should be stored.
    
    Defaults to an SQLite database named `app.db` in the `data` directory (parent of the directory where this file is located at).
    If `replica_id` is set, a subdirectory with the same name as the value of `replica_id` will be added to end of the directories in `database_file_path` (see docs for `replica_ id` for an explanation of the reasoning behind this).
    """

    @property
    def async_db_url(self):
        return f"sqlite+aiosqlite:///{self.database_file_path}"

    @property
    def sync_db_url(self):
        return f"sqlite:///{self.database_file_path}"

    echo_sql: bool = True

    test: bool = False

    project_name: str = "Scraper API"

    log_level: str = "DEBUG"

    replica_id: str | None = None
    """
    If this `replica_id` is set, all logs and persistent data will be written to and read from subdirectories with a name matching `replica_id`.

    This is useful for running multiple copies of the API server on one host machine, e.g. a Docker compose project with multiple 'replicas' (where each service mounts the same 'root volumes').
    """

    api_client_log_dir: str = f"{file_dir.parent.resolve()}/logs/api_clients"
    """
    The directory where logs from any API clients used in the application are stored.

    Defaults to the `logs` directory in the parent directory of the directory containing this file.
    If `replica_id` is set, data will be stored in a subdirectory with the same name as the value of `replica_id`.
    """

    app_log_dir: str = f"{file_dir.parent.resolve()}/logs"
    """
    The directory where 'global' logs from the main application are stored.

    If `replica_id` is set, data will be stored in a subdirectory with the same name as the value of `replica_id`.
    """

    task_log_dir: str = f"{file_dir.parent.resolve()}/logs/tasks"
    """
    The directory where logs for the tasks are stored. Each task will have its own log file named after the task ID.

    Defaults to the `logs` directory in the parent directory of the directory containing this file.
    If `replica_id` is set, data will be stored in a subdirectory with the same name as the value of `replica_id`.
    """

    task_output_dir: str = f"{file_dir.parent.resolve()}/data/task_outputs"
    """
    The directory where the output files for tasks are stored. During processing, each task will have its own JSONL file named after the task ID.
    The JSONL files are compressed using zstd and uploaded to S3 once they reach a certain size or when all inputs have been processed.

    If `replica_id` is set, data will be stored in a subdirectory with the same name as the value of `replica_id`.
    """

    task_progress_dbs_dir: str = f"{file_dir.parent.resolve()}/data/task_progress_dbs"
    """
    The directory where the SQLite databases for task progress tracking are stored.
    1 database file is created and maintained/accessed for each `TaskProcessor` for a particular task ID.
    Each file stores the input items that have not been processed yet as well as the inputs that either resulted in an error or produced no output at all.

    If `replica_id` is set, data will be stored in a subdirectory with the same name as the value of `replica_id`.
    """

    s3_endpoint_url: str
    """
    The endpoint URL for the S3-compatible storage service where the output data of the tasks is stored.
    """

    s3_bucket: str
    """
    The name of the S3 bucket where the output data of the tasks is stored.
    """

    s3_key_id: str
    """
    The access key ID for the S3 bucket where the output data of the tasks is stored.
    """

    s3_secret: str
    """
    The secret access key for the S3 bucket where the output data of the tasks is stored.
    """

    credentials_api_url: str
    """
    The URL of the API that provides credentials for API clients used throughout the application.

    At the time of this writing, this only includes client ID + secret for the Spotify API client.
    """


settings = Settings()  # type: ignore

if settings.replica_id:
    settings.database_file_path = os.path.join(
        os.path.dirname(settings.database_file_path),
        settings.replica_id,
        os.path.basename(settings.database_file_path),
    )
    settings.api_client_log_dir = os.path.join(
        settings.api_client_log_dir, settings.replica_id
    )
    settings.app_log_dir = os.path.join(settings.app_log_dir, settings.replica_id)
    settings.task_log_dir = os.path.join(settings.task_log_dir, settings.replica_id)
    settings.task_output_dir = os.path.join(
        settings.task_output_dir, settings.replica_id
    )
    settings.task_progress_dbs_dir = os.path.join(
        settings.task_progress_dbs_dir, settings.replica_id
    )

DB_DIR = os.path.dirname(settings.database_file_path)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

TASK_OUTPUT_DIR = settings.task_output_dir
if not os.path.exists(TASK_OUTPUT_DIR):
    os.makedirs(TASK_OUTPUT_DIR)

TASK_PROGRESS_DB_DIR = settings.task_progress_dbs_dir
if not os.path.exists(TASK_PROGRESS_DB_DIR):
    os.makedirs(TASK_PROGRESS_DB_DIR)

APP_LOG_DIR = settings.app_log_dir
if not os.path.exists(APP_LOG_DIR):
    os.makedirs(APP_LOG_DIR)

TASK_LOG_DIR = settings.task_log_dir
if not os.path.exists(TASK_LOG_DIR):
    os.makedirs(TASK_LOG_DIR)

PUBLIC_IP = get_public_ip()

if not os.path.exists(settings.api_client_log_dir):
    os.makedirs(settings.api_client_log_dir)


def get_log_level(log_level: str) -> int:
    if log_level == "DEBUG":
        return logging.DEBUG
    if log_level == "INFO":
        return logging.INFO
    if log_level == "WARNING":
        return logging.WARNING
    if log_level == "ERROR":
        return logging.ERROR
    if log_level == "CRITICAL":
        return logging.CRITICAL
    raise ValueError(f"Invalid log level: {log_level}")


def setup_logger(
    name: str,
    file_dir: str | None = None,
    level: int = get_log_level(settings.log_level),
    log_to_console: bool = True,
) -> logging.Logger:
    if level not in [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]:
        raise ValueError(
            "Invalid log level provided. Make sure to use one of the constants from the logging module!"
        )

    logger = logging.getLogger(name)
    if logger.handlers:
        raise ValueError(
            f"Logger '{name}' already has handlers attached! This is probably an error as every logger should only be configured once."
        )
    logger.setLevel(level)

    if log_to_console:
        formatter = logging.Formatter(
            "[%(levelname)s] %(name)s, %(asctime)s: %(message)s"
        )
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(level)
        logger.addHandler(ch)

    if file_dir:
        abs_dir_path = os.path.abspath(file_dir)
        if not os.path.exists(abs_dir_path):
            raise ValueError(
                f"Log file parent directory for '{name}' ({abs_dir_path}) does not exist!"
            )
        if not os.path.isdir(abs_dir_path):
            raise ValueError(
                f"Specified log file parent directory for '{name}' ({abs_dir_path}) is not a directory!"
            )
        file_path = os.path.join(abs_dir_path, f"{name}.log")
        fh = logging.FileHandler(file_path)
        formatter = logging.Formatter("[%(levelname)s] %(asctime)s: %(message)s")
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    return logger


app_logger = setup_logger("app", file_dir=APP_LOG_DIR)
