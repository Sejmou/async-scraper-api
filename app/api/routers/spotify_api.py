from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, model_validator, ValidationError
from app.utils.spotify_api import SpotifyAPIClient, CredentialsBlockedException

router = APIRouter(prefix="/spotify-api")


def handle_credentials_blocked_exception(e: CredentialsBlockedException):
    info_dict = {
        "message": e.message,
    }
    if e.blocked_until:
        info_dict["blocked_until"] = e.blocked_until.isoformat()
    raise HTTPException(503, info_dict)


@router.post("/tracks", status_code=202)
def schedule_fetching_of_tracks(
    payload: LoadTracksPayload,
    background_tasks: BackgroundTasks,
):
    track_ids = payload.track_ids
    region = payload.region
    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("tracks")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(fetch_and_upload_tracks, client, track_ids, region)
    region_str = f" in region {region}" if region else ""
    return {
        "message": f"Fetching tracks{region_str} from Spotify API for {len(track_ids)} IDs."
    }


@router.post("/audio-features", status_code=202)
def schedule_fetching_of_audio_features(
    payload: LoadAudioFeaturesPayload, background_tasks: BackgroundTasks
):
    track_ids = payload.track_ids
    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("audio-features")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(fetch_and_upload_audio_features, client, track_ids)
    return {
        "message": f"Fetching audio features from Spotify API for {len(track_ids)} tracks."
    }


@router.post("/artists", status_code=202)
def schedule_fetching_of_artists(
    payload: LoadArtistDataPayload,
    background_tasks: BackgroundTasks,
):
    artist_ids = payload.artist_ids
    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("artists")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(fetch_and_upload_artists, client, artist_ids)
    return {
        "message": f"Fetching artist metadata from Spotify API for {len(artist_ids)} artists."
    }


@router.post("/related-artists", status_code=202)
def schedule_fetching_of_related_artists(
    payload: LoadArtistDataPayload,
    background_tasks: BackgroundTasks,
):
    artist_ids = payload.artist_ids
    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("artists")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(fetch_and_upload_related_artists, client, artist_ids)
    return {
        "message": f"Fetching related artists from Spotify API for {len(artist_ids)} artists."
    }


@router.post("/artist-albums", status_code=202)
def schedule_fetching_of_artist_albums(
    payload: LoadArtistAlbumsPayload,
    background_tasks: BackgroundTasks,
):
    artist_ids = payload.artist_ids
    albums = payload.albums
    singles = payload.singles
    compilations = payload.compilations
    appears_on = payload.appears_on
    region = payload.region

    include_group_strs = []
    if albums:
        include_group_strs.append("album")
    if singles:
        include_group_strs.append("single")
    if compilations:
        include_group_strs.append("compilation")
    if appears_on:
        include_group_strs.append("appears_on")
    includes_str = f"(include_groups aka release types: {','.join(include_group_strs)})"

    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("artists")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)

    background_tasks.add_task(
        fetch_and_upload_artist_albums,
        client,
        artist_ids,
        albums=albums,
        singles=singles,
        compilations=compilations,
        appears_on=appears_on,
        region=region,
    )
    return {
        "message": f"Fetching albums from Spotify API for {len(artist_ids)} artists {includes_str}."
    }


@router.post("/albums", status_code=202)
def schedule_fetching_of_albums(
    payload: LoadAlbumsPayload,
    background_tasks: BackgroundTasks,
):
    album_ids = payload.album_ids
    region = payload.region

    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("albums")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(
        fetch_and_upload_albums,
        client,
        album_ids,
        region=region,
    )

    region_str = f" and region {region}" if region else ""
    return {
        "message": f"Fetching album metadata from Spotify API for {len(album_ids)} album IDs{region_str}."
    }


@router.post("/playlists", status_code=202)
def schedule_fetching_of_playlists(
    payload: LoadPlaylistsPayload,
    background_tasks: BackgroundTasks,
):
    playlist_ids = payload.playlist_ids
    timeout_between_requests = payload.timeout_between_requests

    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("playlists")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(
        fetch_and_upload_playlists,
        client,
        playlist_ids,
    )

    return {
        "message": f"Fetching playlist metadata from Spotify API for {len(playlist_ids)} playlist IDs"
        + (
            f" with timeout between requests of {timeout_between_requests} seconds"
            if timeout_between_requests
            else ""
        )
        + "."
    }


@router.post("/track-search-isrcs", status_code=202)
def schedule_fetching_of_tracks_by_isrcs(
    payload: SearchTracksForISRCsPayload,
    background_tasks: BackgroundTasks,
):
    isrcs = payload.isrcs
    region = payload.region
    client = SpotifyAPIClient(app_logger)
    try:
        client.raise_if_endpoint_blocked("search")
    except CredentialsBlockedException as e:
        handle_credentials_blocked_exception(e)
    background_tasks.add_task(
        search_tracks_for_isrcs_and_upload_matches, client, isrcs, region
    )
    region_str = f" in region {region}" if region else ""
    return {
        "message": f"Searching for tracks in Spotify API for {len(isrcs)} ISRCs{region_str}."
    }
