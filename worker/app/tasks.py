"""RQ task entrypoint — `run_download(job_id)`."""
import logging
import traceback
import uuid
from pathlib import Path

from . import db, r2
from .config import get_settings
from .progress import publish
from .ytdl import cleanup, run_ytdlp

log = logging.getLogger(__name__)


def _emit(job_id: str, **payload) -> None:
    publish(job_id, {"job_id": job_id, **payload})


def _set(job_id: str, **patch) -> None:
    db.update_download(job_id, patch)
    _emit(job_id, **patch)


def extract_transcript(file_path: Path) -> str | None:
    """Reserved for future Whisper integration."""
    return None


def run_download(job_id: str) -> None:
    settings = get_settings()
    row = db.get_download(job_id)
    if not row:
        log.error("Job %s not found", job_id)
        return

    work_dir = Path(settings.temp_dir) / job_id
    try:
        _set(job_id, status="downloading", progress=0)

        def on_progress(d: dict) -> None:
            status = d.get("status")
            if status == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                pct = (downloaded / total * 95) if total else 0
                _emit(job_id, status="downloading", progress=round(pct, 2),
                      eta=d.get("eta"), speed=d.get("speed"))
            elif status == "finished":
                _emit(job_id, status="processing", progress=95)

        result = run_ytdlp(
            url=row["source_url"],
            media_type=row["media_type"],
            quality=row["quality"],
            out_dir=work_dir,
            on_progress=on_progress,
        )

        _set(
            job_id,
            status="uploading",
            progress=96,
            title=result.title,
            thumbnail=result.thumbnail,
            duration=result.duration,
        )

        # Build R2 key: <user>/<job>/<title>.<ext>
        safe_name = result.file_path.name
        key = f"{row['user_id']}/{job_id}/{safe_name}"
        content_type = "audio/mpeg" if result.ext == "mp3" else "video/mp4"
        size = r2.upload_file(result.file_path, key, content_type=content_type)

        public = r2.public_url(key)

        _set(
            job_id,
            status="completed",
            progress=100,
            r2_key=key,
            public_url=public,
            bytes=size,
            error=None,
        )

    except Exception as exc:  # noqa: BLE001
        log.exception("download failed")
        _set(job_id, status="failed", error=f"{type(exc).__name__}: {exc}")
        # re-raise so RQ records the failure and retries fire
        raise
    finally:
        cleanup(work_dir)


def purge_old_downloads(days: int) -> int:
    """Optional housekeeping job: deletes objects + rows older than `days` days."""
    from datetime import datetime, timedelta, timezone

    if days <= 0:
        return 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    sb = db.supabase()
    res = (
        sb.table("downloads")
        .select("id,r2_key")
        .lt("created_at", cutoff)
        .eq("status", "completed")
        .execute()
    )
    rows = res.data or []
    from .r2 import r2_client
    bucket = get_settings().r2_bucket
    for r in rows:
        if r.get("r2_key"):
            try:
                r2_client().delete_object(Bucket=bucket, Key=r["r2_key"])
            except Exception:  # noqa: BLE001
                pass
        sb.table("downloads").update({"status": "deleted"}).eq("id", r["id"]).execute()
    return len(rows)


__all__ = ["run_download", "purge_old_downloads", "extract_transcript"]
_ = uuid  # keep import for future use
