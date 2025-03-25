from logging import Logger
import nodriver as uc
from nodriver import cdp
from nodriver.cdp.network import Request
from asyncio import sleep


async def get_spotify_related_artists_request_blueprint(
    artist_id: str, logger: Logger
) -> Request:
    browser = await uc.start()
    page = await browser.get(f"https://open.spotify.com/artist/{artist_id}/related")

    req_data: Request | None = None

    def handle_request(data: cdp.network.RequestWillBeSent):
        req = data.request
        if (
            req.url.startswith(
                "https://api-partner.spotify.com/pathfinder/v1/query?operationName=queryArtistRelated"
            )
            and req.method == "GET"
        ):
            logger.info("Found related artists request")
            nonlocal req_data
            req_data = req

    page.add_handler(cdp.network.RequestWillBeSent, handle_request)

    logger.info("Getting cookie banner")
    cookie_banner = await page.find("Accept cookies", best_match=True)
    if cookie_banner:
        logger.info("Clicking cookie banner")
        await cookie_banner.click()
    else:
        logger.info("No cookie banner found")

    while not req_data:
        logger.info("Waiting for request data")
        await sleep(1)

    browser.stop()
    return req_data
