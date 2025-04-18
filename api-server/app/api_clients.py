from app.config import settings, api_client_config, setup_logger
from app.utils.spotify_api import SpotifyAPIClient, SpotifyAPICredentials
from app.utils.dummy_api import DummyAPIClient
from app.utils.api_bans import ban_handler
from app.utils.spotify_internal import SpotifyInternalAPIClient

sp_api_logger = setup_logger("spotify-api", file_dir=settings.api_client_log_dir)
sp_api_creds = api_client_config.spotify_api

spotify_api_client = SpotifyAPIClient(
    credentials=SpotifyAPICredentials(
        client_id=sp_api_creds.client_id, client_secret=sp_api_creds.client_secret
    ),
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
