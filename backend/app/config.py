from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
