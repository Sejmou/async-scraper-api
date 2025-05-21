from app.tasks.models import TaskExecutionMetaModel, get_task_json_schema


def test_spotify_api_tracks_task_json_schema():
    get_task_json_schema(data_source="spotify-api", task_type="tracks")


def test_spotify_api_tracks_task_validation():
    task = TaskExecutionMetaModel.model_validate(
        {
            "data_source": "spotify-api",
            "task_type": "tracks",
            "params": {
                "region": "us",
            },
            "inputs": ["06HL4z0CvFAxyc27GXpf02", "1uNFoZAHBGtllmzznpCI3s"],
        }
    ).root
    assert task.data_source == "spotify-api"
    assert task.task_type == "tracks"
    assert task.params.region == "us"
    assert len(task.inputs) == 2
    assert task.inputs[0] == "06HL4z0CvFAxyc27GXpf02"
    assert task.inputs[1] == "1uNFoZAHBGtllmzznpCI3s"
