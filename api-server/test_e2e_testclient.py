"""
This should be end-to-end tests that more or less replicate how things would work on a live server, but they don't (for instance, the task creation request blocks, while it doesn't on a live server)
TODO: figure out why.
"""

import random
import string
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def generate_spotify_id(length: int = 22) -> str:
    base62_chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return "".join(random.choices(base62_chars, k=length))


def test_create_big_task():
    """
    Test the creation of a big task. The input IDs are randomly generated. They should be processed in the background (i.e. task creation should be fast and this test should finish quickly).
    """
    id_count = 100000

    random_ids = [generate_spotify_id() for _ in range(id_count)]

    start = time.perf_counter()
    response = client.post(
        "/tasks/create",
        json={
            "data_source": "spotify-api",
            "task_type": "tracks",
            "params": {
                "region": "us",
            },
            "inputs": random_ids,
        },
    )
    end = time.perf_counter()
    time_passed = end - start
    print(f"Task creation took {time_passed:.2f} seconds")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "paused"
    assert time_passed < 1, "Task creation took too long"
