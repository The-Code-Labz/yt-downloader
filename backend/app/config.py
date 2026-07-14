import logging
from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_schema: str = "neuroarchive"

    # R2
    r2_endpoint: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str
    r2_public_base_url: str | None = None

    @field_validator("r2_endpoint")
    @classmethod
    def _strip_endpoint_path(cls, v: str) -> str:
        """boto3 path-style-addresses R2 (bucket becomes the first URL path
        segment). A stray path on R2_ENDPOINT (e.g. .../neuroarchive) silently
        folds into every uploaded object's key as a duplicate bucket-name
        prefix — the S3 endpoint must be scheme+host only, never bucket-scoped."""
        parts = urlsplit(v)
        if parts.path not in ("", "/"):
            log.warning(
                "R2_ENDPOINT=%s has a path component (%s); stripping it. "
                "The endpoint must NOT include the bucket name — set R2_BUCKET "
                "instead, or every object key gets a silent '%s/' prefix.",
                v, parts.path, parts.path.strip("/"),
            )
            v = f"{parts.scheme}://{parts.netloc}"
        return v

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # API
    cors_origins: str = "http://localhost:5173"
    signed_url_ttl_seconds: int = 3600
    auto_delete_days: int = 0

    # Shared-secret auth for POST /admin/cookies (separate from Supabase JWTs
    # since it's called by an unattended home-network script, not a browser
    # session). Left unset by default — the endpoint 404s until configured.
    admin_secret: str | None = None
    # Must match the worker's YTDLP_COOKIES_FILE for the push to take effect;
    # written atomically (tmp file + rename) so the worker never reads a
    # half-written file mid-request.
    cookies_file_path: str = "/data/cookies/cookies.txt"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
