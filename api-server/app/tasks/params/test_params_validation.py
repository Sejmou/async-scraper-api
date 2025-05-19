from app.tasks.params import parse_task_params


def test_spotify_api_tracks():
    raw_value = {"data_source": "spotify-api", "task_type": "tracks", "region": "de"}
    params = parse_task_params(raw_value)
    assert params.task_type == "tracks"
    assert params.data_source == "spotify-api"
    assert params.region == "de"
