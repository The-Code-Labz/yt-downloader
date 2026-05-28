"""Publish progress events to Redis pub/sub so the API can relay over WebSocket."""
import json
from functools import lru_cache
from typing import Any

import redis

from .config import get_settings


@lru_cache
def redis_conn() -> redis.Redis:
    return redis.from_url(get_settings().redis_url)


def publish(job_id: str, payload: dict[str, Any]) -> None:
    try:
        redis_conn().publish(f"job:{job_id}", json.dumps(payload, default=str))
    except Exception:  # noqa: BLE001
        # Never let pub/sub errors kill a download
        pass
