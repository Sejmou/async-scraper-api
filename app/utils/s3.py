import os
from contextlib import asynccontextmanager
import aioboto3

from app.config import settings

S3_ENDPOINT_URL = settings.s3_endpoint_url
S3_BUCKET = settings.s3_bucket
S3_KEY_ID = settings.s3_key_id
S3_SECRET = settings.s3_secret

session = aioboto3.Session(aws_access_key_id=S3_KEY_ID, aws_secret_access_key=S3_SECRET)


@asynccontextmanager
async def s3_service():
    async with session.resource("s3", endpoint_url=S3_ENDPOINT_URL) as s3:
        yield s3


@asynccontextmanager
async def s3_client():
    async with session.client("s3", endpoint_url=S3_ENDPOINT_URL) as s3:
        yield s3


async def upload_file(local_path: str, s3_key: str, remove_after_upload=False) -> str:
    """
    Uploads a local file to S3.

    :param local_path: The path to the local file
    :param s3_key: The S3 key under which the file should be uploaded
    :return: The S3 key under which the file was uploaded
    """
    async with s3_service() as s3:
        bucket = await s3.Bucket(S3_BUCKET)
        await bucket.upload_file(local_path, s3_key)
        if remove_after_upload:
            os.remove(local_path)
        return s3_key
