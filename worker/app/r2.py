"""R2 uploader."""
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config

from .config import get_settings


@lru_cache
def r2_client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.r2_endpoint,
        aws_access_key_id=s.r2_access_key_id,
        aws_secret_access_key=s.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def upload_file(local_path: str | Path, key: str, content_type: str | None = None) -> int:
    s = get_settings()
    extra: dict = {}
    if content_type:
        extra["ContentType"] = content_type
    p = Path(local_path)
    size = p.stat().st_size
    r2_client().upload_file(str(p), s.r2_bucket, key, ExtraArgs=extra or None)
    return size


def public_url(key: str) -> str | None:
    s = get_settings()
    if s.r2_public_base_url:
        return f"{s.r2_public_base_url.rstrip('/')}/{key}"
    return None
