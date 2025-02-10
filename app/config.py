import os
from pathlib import Path
from typing import Tuple, Type
import logging
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from app.utils.misc import get_public_ip

file_dir = Path(__file__).parent


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"

    echo_sql: bool = True

    test: bool = False

    project_name: str = "Scraper API v2"

    log_level: str = "DEBUG"

    api_client_log_dir: str = f"{file_dir.parent.resolve()}/logs/api_clients"
    """
    The directory where logs from any API clients used in the application are stored.

    Defaults to the `logs` directory in the parent directory of the directory containing this file.
    """

    task_output_dir: str = f"{file_dir.parent.resolve()}/task_outputs"
    """
    The directory where the output files for tasks are stored. During processing, each task will have its own JSONL file named after the task ID.
    The JSONL files are compressed using zstd and uploaded to S3 once they reach a certain size or when all inputs have been processed.
    """

    task_progress_dbs_dir: str = f"{file_dir.parent.resolve()}/task_progress"
    """
    The directory where the SQLite databases for task progress tracking are stored.
    1 database file is created and maintained/accessed for each `TaskProcessor` for a particular task ID.
    Each file stores the input items that have not been processed yet as well as the inputs that either resulted in an error or produced no output at all.
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


settings = Settings()  # type: ignore

PUBLIC_IP = get_public_ip()

if not os.path.exists(settings.api_client_log_dir):
    os.makedirs(settings.api_client_log_dir)


class SpotifyAPICredentials(BaseSettings):
    client_id: str
    client_secret: str


class APIClientConfig(BaseSettings):
    """
    Stores configuration for the API clients used for the scraper tasks in the application.
    """

    # code adapted from TOML example at https://docs.pydantic.dev/latest/concepts/pydantic_settings/#other-settings-source

    spotify_api: SpotifyAPICredentials

    model_config = SettingsConfigDict(yaml_file="api-client-config.yml", extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # the way we have set this up, config is ONLY loaded from the YAML file
        return (YamlConfigSettingsSource(settings_cls),)


api_client_config = APIClientConfig()  # type: ignore


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
