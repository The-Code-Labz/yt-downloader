from functools import lru_cache
from typing import Any

from supabase import Client, create_client
from supabase.client import ClientOptions

from .config import get_settings


@lru_cache
def supabase() -> Client:
    s = get_settings()
    return create_client(
        s.supabase_url,
        s.supabase_service_role_key,
        options=ClientOptions(schema=s.supabase_schema),
    )


def get_download(job_id: str) -> dict[str, Any] | None:
    res = supabase().table("downloads").select("*").eq("id", job_id).limit(1).execute()
    return (res.data or [None])[0]


def update_download(job_id: str, patch: dict[str, Any]) -> None:
    supabase().table("downloads").update(patch).eq("id", job_id).execute()
