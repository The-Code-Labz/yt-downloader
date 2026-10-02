"""Shared DB-row -> API-model serialization (used by both the user and agent routes)."""
from . import r2
from .schemas import DownloadOut


def serialize_download(row: dict, include_signed_url: bool = False) -> DownloadOut:
    signed = None
    if include_signed_url and row.get("r2_key") and row.get("status") == "completed":
        try:
            signed = r2.signed_url(row["r2_key"])
        except Exception:  # noqa: BLE001
            signed = None
    return DownloadOut(**row, signed_url=signed)
