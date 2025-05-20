from app.tasks.models import get_task_json_schema


def test_spotify_api_tracks_task_json_schema():
    schema = get_task_json_schema(data_source="spotify-api", task_type="tracks")
