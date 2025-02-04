from datetime import datetime
from pydantic import BaseModel

from app.db.models import APIRequestMeta, JSONValue
from app.db import sessionmanager


class APIRequestMetaSchema(BaseModel):
    url: str
    status_code: int
    sent_at: datetime
    received_at: datetime
    ip: str
    details: JSONValue = None


async def persist_request_meta_in_db(
    request_meta: APIRequestMetaSchema,
):
    db_meta = APIRequestMeta(
        url=request_meta.url,
        status_code=request_meta.status_code,
        sent_at=request_meta.sent_at,
        received_at=request_meta.received_at,
        ip=request_meta.ip,
        details=request_meta.details,
    )
    async with sessionmanager.session() as db_session:
        db_session.add(db_meta)
        await db_session.commit()
