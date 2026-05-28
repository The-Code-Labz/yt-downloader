from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


MediaType = Literal["audio", "video"]
Quality = Literal["best", "1080p", "720p", "audio"]
JobStatus = Literal[
    "queued", "downloading", "processing", "uploading", "completed", "failed", "deleted"
]


class DownloadCreate(BaseModel):
    url: HttpUrl
    media_type: MediaType = "video"
    quality: Quality = "best"


class DownloadOut(BaseModel):
    id: str
    user_id: str
    source_url: str
    title: str | None = None
    thumbnail: str | None = None
    duration: int | None = None
    media_type: MediaType
    quality: Quality
    status: JobStatus
    progress: float = 0
    error: str | None = None
    r2_key: str | None = None
    public_url: str | None = None
    bytes: int | None = None
    signed_url: str | None = None
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    status: str = "ok"
