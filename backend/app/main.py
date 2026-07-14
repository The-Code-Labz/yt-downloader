"""NeuroArchive FastAPI entrypoint."""
import logging

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .deps import get_current_user
from .routes import admin, downloads, health
from .ws import stream_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neuroarchive")

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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all so unexpected errors still get a body + CORS headers.

    Without this, Starlette's default ServerErrorMiddleware returns a bare
    500 that bypasses CORSMiddleware entirely — the browser then reports a
    (misleading) CORS failure instead of the real backend error. Registering
    a handler here routes the exception through ExceptionMiddleware instead,
    so the response still flows back out through CORSMiddleware.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


app.include_router(health.router, tags=["meta"])
app.include_router(downloads.router, tags=["downloads"])
app.include_router(admin.router)


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
