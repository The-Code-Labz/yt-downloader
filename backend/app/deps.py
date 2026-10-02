"""Auth dependencies — validates a Supabase-issued JWT, or an agent API key."""
import secrets as pysecrets

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing sub")
    return {"id": user_id, "email": payload.get("email"), "token": token}


def get_agent_user(
    x_agent_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Shared-secret auth for the agent API (/agent/*) — no Supabase session.

    Mirrors routes/admin.py's `_require_admin`: unconfigured => 404 (don't
    leak that the feature exists), mismatch => 401.
    """
    if not settings.agent_api_key or not settings.agent_user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not x_agent_key or not pysecrets.compare_digest(x_agent_key, settings.agent_api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid agent key")
    return {"id": settings.agent_user_id, "email": "agent"}
