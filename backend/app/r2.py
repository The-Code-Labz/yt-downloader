"""Cloudflare R2 client (S3-compatible) — used by the API for signed URLs and deletes.

Uploads happen in the worker; this module only generates URLs and deletes objects.
"""
from functools import lru_cache

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


def signed_url(key: str, ttl: int | None = None) -> str:
    s = get_settings()
    if s.r2_public_base_url:
        # Permanent URL via a custom domain bound to the bucket
        base = s.r2_public_base_url.rstrip("/")
        return f"{base}/{key}"
    return r2_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": s.r2_bucket, "Key": key},
        ExpiresIn=ttl or s.signed_url_ttl_seconds,
    )


def delete_object(key: str) -> None:
    s = get_settings()
    r2_client().delete_object(Bucket=s.r2_bucket, Key=key)
