"""Agent-facing REST API — same job model as /download & /jobs, but authed via
a shared secret (`X-Agent-Key`) instead of a Supabase session, so an unattended
agent with no user login can start a download and pull the result once ready.

All jobs created here are owned by `settings.agent_user_id` (see config.py).
404s entirely when AGENT_API_KEY / AGENT_USER_ID aren't set.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from .. import db, r2
from ..deps import get_agent_user
from ..queue import enqueue_download
from ..schemas import DownloadCreate, DownloadOut
from ..serialize import serialize_download

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/download", response_model=DownloadOut, status_code=status.HTTP_201_CREATED)
def agent_create_download(payload: DownloadCreate, user=Depends(get_agent_user)) -> DownloadOut:
    """Start a download job. Poll GET /agent/job/{id} until status=='completed',
    then pull the file via its `signed_url` or GET /agent/job/{id}/file."""
    row = db.insert_download(
        {
            "user_id": user["id"],
            "source_url": str(payload.url),
            "media_type": payload.media_type,
            "quality": payload.quality,
            "status": "queued",
            "progress": 0,
        }
    )
    enqueue_download(row["id"])
    return serialize_download(row)


@router.get("/jobs", response_model=list[DownloadOut])
def agent_list_jobs(user=Depends(get_agent_user)) -> list[DownloadOut]:
    rows = db.list_downloads(user["id"])
    return [serialize_download(r, include_signed_url=True) for r in rows]


@router.get("/job/{job_id}", response_model=DownloadOut)
def agent_get_job(job_id: str, user=Depends(get_agent_user)) -> DownloadOut:
    row = db.get_download(job_id, user["id"])
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return serialize_download(row, include_signed_url=True)


@router.get("/job/{job_id}/file")
def agent_pull_job_file(job_id: str, user=Depends(get_agent_user)) -> RedirectResponse:
    """Convenience for `curl -L`/`wget` — 302s straight to a fresh signed R2 URL."""
    row = db.get_download(job_id, user["id"])
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if row.get("status") != "completed" or not row.get("r2_key"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Job is '{row.get('status')}', not completed yet")
    return RedirectResponse(r2.signed_url(row["r2_key"]), status_code=status.HTTP_302_FOUND)


@router.delete("/job/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def agent_delete_job(job_id: str, user=Depends(get_agent_user)) -> None:
    row = db.get_download(job_id, user["id"])
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if row.get("r2_key"):
        try:
            r2.delete_object(row["r2_key"])
        except Exception:  # noqa: BLE001
            pass
    db.soft_delete(job_id, user["id"])
