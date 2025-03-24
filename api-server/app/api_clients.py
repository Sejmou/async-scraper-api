from app.config import settings, api_client_config, setup_logger
from app.utils.spotify_api import SpotifyAPIClient, SpotifyAPICredentials
from app.utils.api_bans import ban_handler

sp_api_logger = setup_logger("spotify_api_client", file_dir=settings.api_client_log_dir)
sp_api_creds = api_client_config.spotify_api

spotify_api_client = SpotifyAPIClient(
    credentials=SpotifyAPICredentials(
        client_id=sp_api_creds.client_id, client_secret=sp_api_creds.client_secret
    ),
    logger=sp_api_logger,
    ban_handler=ban_handler,
)

spotify_internal_logger = setup_logger(
    "spotify_internal", file_dir=settings.api_client_log_dir
)
