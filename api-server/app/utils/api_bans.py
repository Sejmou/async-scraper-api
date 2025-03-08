from app.db.models import APIEndpointBlock
from app.db import sessionmanager
from sqlalchemy import select
from datetime import datetime, timezone


class TemporaryBanError(Exception):
    def __init__(self, message: str, blocked_until: datetime):
        super().__init__(message)
        self.blocked_until = blocked_until


class APIBanHandler:
    """
    A class that handles temporary bans of particular API endpoints for various datasources as consequence of making too many requests too quickly.

    At the time of this writing, this is only relevant for the Spotify API as it doesn't document its rate limits in detail anywhere
    but we need to make sure no additional requests are made if an endpoint is blocked (otherwise the ban will be extended).
    """

    async def raise_if_blocked(self, data_source: str, endpoint: str):
        async with sessionmanager.session() as db_session:
            stmt = (
                select(APIEndpointBlock)
                .where(APIEndpointBlock.data_source == data_source)
                .where(APIEndpointBlock.endpoint == endpoint)
                .where(APIEndpointBlock.blocked_until > datetime.now(timezone.utc))
            )
            block = await db_session.scalar(stmt)
            if block:
                raise TemporaryBanError(
                    f"'{endpoint}' endpoint of {data_source} is blocked until {block.blocked_until}",
                    blocked_until=block.blocked_until,
                )

    async def block(
        self,
        data_source: str,
        endpoint: str,
        block_until: datetime,
        details: dict | None = None,
    ):
        async with sessionmanager.session() as db_session:
            block = APIEndpointBlock(
                data_source=data_source,
                endpoint=endpoint,
                blocked_at=datetime.now(timezone.utc),
                blocked_until=block_until,
                details=details,
            )
            db_session.add(block)
            await db_session.commit()

    async def unblock(self, data_source: str, endpoint: str):
        async with sessionmanager.session() as db_session:
            stmt = (
                select(APIEndpointBlock)
                .where(APIEndpointBlock.data_source == data_source)
                .where(APIEndpointBlock.endpoint == endpoint)
            )
            block = await db_session.scalar(stmt)
            if block is not None:
                await db_session.delete(block)
            else:
                raise ValueError(f"Block for {data_source} {endpoint} does not exist")
            await db_session.commit()


ban_handler = APIBanHandler()
