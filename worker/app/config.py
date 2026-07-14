import logging
from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_schema: str = "neuroarchive"

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

    redis_url: str = "redis://redis:6379/0"
    temp_dir: str = "/tmp/neuroarchive"

    # Path to a Netscape-format cookies.txt (mounted read-only) used to get
    # yt-dlp past YouTube's "Sign in to confirm you're not a bot" bot-check.
    # Left unset by default; ytdl.py no-ops if the path is empty or missing.
    # Re-read from disk on every job — no restart needed when the file changes
    # (see scripts/refresh_cookies.py for automated refresh).
    ytdlp_cookies_file: str | None = None

    # Proxy yt-dlp's outbound requests through, e.g. a SOCKS5 tunnel back to a
    # residential/home network with better YouTube IP reputation than a cloud
    # host. Accepts any yt-dlp/urllib3 proxy URL: socks5://[user:pass@]host:port
    # or http://[user:pass@]host:port. Left unset by default (direct egress).
    ytdlp_proxy: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
