"""NeuroArchive FastAPI entrypoint."""
import logging

from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .deps import get_current_user
from .routes import downloads, health
from .ws import stream_job

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="NeuroArchive API",
    version="0.1.0",
    description="Self-hosted YouTube archive — for content you own or are authorized to archive.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["meta"])
app.include_router(downloads.router, tags=["downloads"])


@app.websocket("/ws/jobs/{job_id}")
async def ws_jobs(ws: WebSocket, job_id: str) -> None:
    """Realtime progress for a single job.

    Auth is enforced by query param `?token=...` to keep things browser-friendly.
    """
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return
    # Reuse the same JWT validator
    try:
        get_current_user(authorization=f"Bearer {token}", settings=settings)
    except Exception:  # noqa: BLE001
        await ws.close(code=4401)
        return
    await stream_job(ws, job_id)
