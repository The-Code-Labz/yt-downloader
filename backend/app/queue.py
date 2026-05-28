"""Redis + RQ glue for enqueueing download jobs."""
from functools import lru_cache

import redis
from rq import Queue, Retry

from .config import get_settings


QUEUE_NAME = "neuroarchive"


@lru_cache
def redis_conn() -> redis.Redis:
    return redis.from_url(get_settings().redis_url)


@lru_cache
def queue() -> Queue:
    return Queue(QUEUE_NAME, connection=redis_conn())


def enqueue_download(job_id: str) -> None:
    """Enqueue the worker task by string reference so the worker can resolve it."""
    queue().enqueue(
        "app.tasks.run_download",
        job_id,
        job_id=job_id,                                  # RQ job id == DB row id
        job_timeout=60 * 60,                            # 1h hard cap per download
        retry=Retry(max=3, interval=[10, 60, 300]),
        result_ttl=3600,
        failure_ttl=86400,
    )
