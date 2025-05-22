"""
End-to-end tests running on a live server. Make sure to spin it up beforehand. Also, don't forget to have the test S3 server running (assuming it's MinIO here)!
"""

import os
import time
import boto3
from dotenv import load_dotenv
import pytest
import requests
import duckdb
from app.api.models import TaskProgressModel, DataFetchingTaskModel


API_SERVER_URL = "http://localhost:8000"
S3_SERVER_URL = "http://localhost:9000"

# read S3 credentials from .env file
load_dotenv()
S3_KEY_ID = os.environ["S3_KEY_ID"]
S3_SECRET = os.environ["S3_SECRET"]


@pytest.fixture(scope="session")
def s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=S3_KEY_ID,
        aws_secret_access_key=S3_SECRET,
        endpoint_url=S3_SERVER_URL,
    )


@pytest.fixture(scope="session")
def duckdb_conn():
    con = duckdb.connect(database=":memory:")

    s3_endpoint = S3_SERVER_URL.replace("http://", "").replace("https://", "")
    con.execute(
        "SET s3_region='us-east-1';"
    )  # apparently DuckDB requires a region to be set even though MinIO ignores it
    con.execute(f"SET s3_access_key_id='{S3_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{S3_SECRET}';")
    con.execute(f"SET s3_endpoint='{s3_endpoint}';")
    con.execute("SET s3_url_style='path';")

    if S3_SERVER_URL.startswith("http://"):
        con.execute("SET s3_use_ssl=false;")

    yield con

    # Teardown
    con.close()


def download_file_from_s3(s3_client, bucket_name: str, s3_key: str, local_path: str):
    """
    Downloads a file from S3 to the local filesystem.
    """
    try:
        s3_client.download_file(bucket_name, s3_key, local_path)
        print(f"Downloaded {s3_key} from bucket {bucket_name} to {local_path}")
    except Exception as e:
        print(f"Failed to download {s3_key} from bucket {bucket_name}: {e}")


def create_throw_above_threshold_task(id_count: int, threshold: int):
    """
    Creates a dummy task that accepts a list of non-negative integer IDs and throws an error for every ID above a predetermined threshold.

    This is useful to test the task processing logic in a rather isolated fashion.
    """
    ids = [i + 1 for i in range(id_count)]

    payload = {
        "data_source": "dummy-api",
        "task_type": "throw-above-threshold",
        "params": {
            "threshold": threshold,
        },
        "inputs": ids,
    }

    start = time.perf_counter()
    response = requests.post(f"{API_SERVER_URL}/tasks/create", json=payload)
    end = time.perf_counter()
    time_passed = end - start

    assert response.status_code == 201, response.text
    # task creation should be pretty much independent of the number of provided IDs as they are supposed to be added to the queue in the background anyway
    assert time_passed < 0.5, "Task creation took too long"

    data = response.json()
    return DataFetchingTaskModel.model_validate(data)


def get_tasks():
    """
    Get all tasks from the live API
    """
    start = time.perf_counter()
    response = requests.get(f"{API_SERVER_URL}/tasks")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, dict), "Response is not a dictionary"
    assert "items" in data, "Response does not contain 'items' key"
    assert isinstance(data["items"], list), "'items' is not a list"
    items = data["items"]
    assert len(items) > 0, "No tasks found"
    end = time.perf_counter()
    time_passed = end - start
    print(f"Tasks retrieval took {time_passed:.2f} seconds")
    return [DataFetchingTaskModel.model_validate(item) for item in items]


def get_task(task_id: int):
    """
    Get a task from the live API.
    """
    start = time.perf_counter()
    response = requests.get(f"{API_SERVER_URL}/tasks/{task_id}")
    end = time.perf_counter()
    time_passed = end - start
    print(f"Task retrieval took {time_passed:.2f} seconds")
    assert response.status_code == 200, response.text
    data = response.json()
    return DataFetchingTaskModel.model_validate(data)


def get_task_progress(task_id: int):
    """
    Get the progress of a task from the live API.
    """
    start = time.perf_counter()
    response = requests.get(f"{API_SERVER_URL}/tasks/{task_id}/progress")
    end = time.perf_counter()
    time_passed = end - start
    print(f"Task progress retrieval took {time_passed:.2f} seconds")
    assert response.status_code == 200, response.text
    data = response.json()
    return TaskProgressModel.model_validate(data)


def execute_task(task_id: int):
    """
    Execute a task from the live API.
    """
    response = requests.post(f"{API_SERVER_URL}/tasks/{task_id}/execute")
    assert response.status_code == 200, response.text
    data = response.json()
    return DataFetchingTaskModel.model_validate(data)


# def test_create_big_task():
#     id_count = 500_000
#     task = create_throw_above_threshold_task(id_count, threshold=id_count)

#     start = time.perf_counter()
#     task_progress = get_task_progress(task.id)
#     while task_progress.remaining_count < id_count:
#         print(f"Task progress: {task_progress}")
#         time.sleep(1)
#         task_progress = get_task_progress(task.id)
#     end = time.perf_counter()
#     time_passed = end - start
#     print(f"Final task progress after {time_passed:.2f} seconds: {task_progress}")


def test_task_execution_perfect_task(s3_client, tmp_path, duckdb_conn):
    """
    Test the execution of a 'perfect task' that does not throw any errors.
    """
    id_count = 10
    task = create_throw_above_threshold_task(id_count, threshold=id_count)
    assert task.status == "paused", "Task is not paused after creation"

    task = execute_task(task.id)
    assert task.status == "pending", "Task is not pending immediately after execution"

    while task.status == "pending":
        time.sleep(1)
        print(f"Task status: {task.status}")
        task = get_task(task.id)

    assert (
        task.status == "running"
    ), f"Expected task to transition to 'running' state, but got '{task.status}'"

    task_progress = get_task_progress(task.id)
    while task_progress.remaining_count > 0:
        print(f"Task progress: {task_progress}")
        time.sleep(1)
        task_progress = get_task_progress(task.id)

    assert task_progress.success_count == id_count, "Not all tasks were successful"
    assert task_progress.failure_count == 0, "Some tasks failed"
    assert task_progress.inputs_without_output_count == 0, "Some tasks had no output"

    task = get_task(task.id)
    assert task.status == "done"

    assert len(task.file_uploads) == 1, "Task did not upload any files"
    file_meta = task.file_uploads[0]

    target_file = os.path.join(
        tmp_path, f"task_{task.id}_output_{file_meta.s3_key.split('/')[-1]}"
    )

    # verify the file is downloadable
    download_file_from_s3(
        s3_client,
        file_meta.s3_bucket,
        file_meta.s3_key,
        target_file,
    )

    # inspect the file contents
    # this is actually more convenient when reading from S3 directly with duckdb than via the downloaded file (would otherwise have to write logic to decompress file from .zst etc.)
    duckdb_conn.execute(
        f"""
    CREATE OR REPLACE TABLE task_output AS
    SELECT * FROM read_json('s3://{file_meta.s3_bucket}/{file_meta.s3_key}')
    """
    )
    data = duckdb_conn.execute("SELECT * FROM task_output").fetchall()
    print(data)
    schema = duckdb_conn.execute("DESCRIBE task_output").fetchall()
    print(schema)
    # TODO: actually validate data and schema, for now I was just happy with what I saw printed in the console lol
