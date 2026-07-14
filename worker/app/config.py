from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_schema: str = "neuroarchive"

    r2_endpoint: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str
    r2_public_base_url: str | None = None

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
