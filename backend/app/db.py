"""Thin wrapper around the Supabase Python client using the service-role key.

Service-role bypasses RLS, so we always filter by user_id ourselves.
All tables live in a custom schema (default: `neuroarchive`) selected via
``ClientOptions(schema=...)`` so PostgREST routes to the right namespace.
"""
from functools import lru_cache
from typing import Any

from supabase.client import ClientOptions

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def supabase() -> Client:
    s = get_settings()
    return create_client(
        s.supabase_url,
        s.supabase_service_role_key,
        options=ClientOptions(schema=s.supabase_schema),
    )


TABLE = "downloads"


def insert_download(row: dict[str, Any]) -> dict[str, Any]:
    res = supabase().table(TABLE).insert(row).execute()
    return res.data[0]


def list_downloads(user_id: str) -> list[dict[str, Any]]:
    res = (
        supabase()
        .table(TABLE)
        .select("*")
        .eq("user_id", user_id)
        .neq("status", "deleted")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def get_download(job_id: str, user_id: str) -> dict[str, Any] | None:
    res = (
        supabase()
        .table(TABLE)
        .select("*")
        .eq("id", job_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def update_download(job_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    res = supabase().table(TABLE).update(patch).eq("id", job_id).execute()
    return (res.data or [None])[0]


def soft_delete(job_id: str, user_id: str) -> None:
    supabase().table(TABLE).update({"status": "deleted"}).eq("id", job_id).eq("user_id", user_id).execute()
