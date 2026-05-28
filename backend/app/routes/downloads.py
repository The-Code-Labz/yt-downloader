"""REST endpoints for download jobs."""
from fastapi import APIRouter, Depends, HTTPException, status

from .. import db, r2
from ..deps import get_current_user
from ..queue import enqueue_download
from ..schemas import DownloadCreate, DownloadOut

router = APIRouter()


def _serialize(row: dict, include_signed_url: bool = False) -> DownloadOut:
    signed = None
    if include_signed_url and row.get("r2_key") and row.get("status") == "completed":
        try:
            signed = r2.signed_url(row["r2_key"])
        except Exception:  # noqa: BLE001
            signed = None
    return DownloadOut(**row, signed_url=signed)


@router.post("/download", response_model=DownloadOut, status_code=status.HTTP_201_CREATED)
def create_download(payload: DownloadCreate, user=Depends(get_current_user)) -> DownloadOut:
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
    return _serialize(row)


@router.get("/jobs", response_model=list[DownloadOut])
def list_jobs(user=Depends(get_current_user)) -> list[DownloadOut]:
    rows = db.list_downloads(user["id"])
    return [_serialize(r, include_signed_url=True) for r in rows]


@router.get("/job/{job_id}", response_model=DownloadOut)
def get_job(job_id: str, user=Depends(get_current_user)) -> DownloadOut:
    row = db.get_download(job_id, user["id"])
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return _serialize(row, include_signed_url=True)


@router.delete("/job/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, user=Depends(get_current_user)) -> None:
    row = db.get_download(job_id, user["id"])
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if row.get("r2_key"):
        try:
            r2.delete_object(row["r2_key"])
        except Exception:  # noqa: BLE001
            pass  # don't block delete if object was already gone
    db.soft_delete(job_id, user["id"])
