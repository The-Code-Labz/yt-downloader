"""WebSocket relay: subscribes to Redis pub/sub and forwards to clients."""
import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect

from .config import get_settings

log = logging.getLogger(__name__)


def channel(job_id: str) -> str:
    return f"job:{job_id}"


async def stream_job(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    redis = aioredis.from_url(get_settings().redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel(job_id))
    try:
        # Push a hello so client knows connection is live
        await ws.send_json({"type": "hello", "job_id": job_id})
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)
            if msg is None:
                await ws.send_json({"type": "ping"})
                continue
            try:
                payload = json.loads(msg["data"])
            except (ValueError, TypeError):
                payload = {"raw": msg["data"]}
            await ws.send_json({"type": "progress", **payload})
            if payload.get("status") in {"completed", "failed"}:
                break
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception:  # noqa: BLE001
        log.exception("ws stream error")
    finally:
        try:
            await pubsub.unsubscribe(channel(job_id))
            await pubsub.close()
            await redis.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            await ws.close()
        except Exception:  # noqa: BLE001
            pass
