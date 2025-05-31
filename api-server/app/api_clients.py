from app.config import settings, setup_logger
from app.utils.spotify_api import (
    SpotifyAPIClient,
)
from app.utils.dummy_api import DummyAPIClient
from app.utils.api_bans import ban_handler
from app.utils.spotify_internal import SpotifyInternalAPIClient

sp_api_logger = setup_logger("spotify-api", file_dir=settings.api_client_log_dir)

spotify_api_client = SpotifyAPIClient(
    credentials_api_url=settings.credentials_api_url,
    logger=sp_api_logger,
    ban_handler=ban_handler,
)

spotify_internal_logger = setup_logger(
    "spotify-internal", file_dir=settings.api_client_log_dir
)

spotify_internal_api_client = SpotifyInternalAPIClient(
    logger=spotify_internal_logger,
)

dummy_api_client_logger = setup_logger(
    "dummy-api", file_dir=settings.api_client_log_dir
)
dummy_api_client = DummyAPIClient(
    logger=dummy_api_client_logger,
)
