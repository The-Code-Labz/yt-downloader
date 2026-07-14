"""Unattended-script endpoints — auth is a shared secret header, not a Supabase JWT.

Currently just cookie refresh: a home-network script (scripts/refresh_cookies.py)
pulls a live Netscape cookies.txt straight from a real, already-logged-in browser
and PUTs it here on a schedule, so YouTube's bot-check cookies stay fresh without
ever touching the deploy host or requiring a redeploy.
"""
import logging
import os
import secrets as pysecrets
import tempfile

from fastapi import APIRouter, Header, HTTPException, Request, status

from ..config import get_settings

log = logging.getLogger("neuroarchive.admin")
router = APIRouter(prefix="/admin", tags=["admin"])

MAX_COOKIES_BYTES = 256 * 1024  # generous — a real cookies.txt is a few KB


def _require_admin(x_admin_secret: str | None) -> None:
    settings = get_settings()
    if not settings.admin_secret:
        # Not configured — treat as not-found rather than leaking that the
        # feature exists but is unreachable.
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not x_admin_secret or not pysecrets.compare_digest(x_admin_secret, settings.admin_secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin secret")


@router.put("/cookies")
async def put_cookies(
    request: Request,
    x_admin_secret: str | None = Header(default=None),
) -> dict:
    _require_admin(x_admin_secret)
    body = await request.body()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty body")
    if len(body) > MAX_COOKIES_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "cookies.txt too large")
    text = body.decode("utf-8", errors="replace")
    # Cheap sanity check so a bad push can't silently brick the good cookies
    # already on disk — a real Netscape export always has this header or at
    # least a youtube.com/google.com cookie line.
    if "Netscape HTTP Cookie File" not in text and "youtube.com" not in text and ".google.com" not in text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Doesn't look like a Netscape cookies.txt")

    settings = get_settings()
    target = settings.cookies_file_path
    target_dir = os.path.dirname(target)
    os.makedirs(target_dir, exist_ok=True)

    # Atomic write: tmp file in the same dir + os.replace, so the worker
    # (reading the same path on every job) never observes a partial file.
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".cookies-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    log.info("cookies.txt refreshed via /admin/cookies (%d bytes)", len(body))
    return {"ok": True, "bytes": len(body)}
