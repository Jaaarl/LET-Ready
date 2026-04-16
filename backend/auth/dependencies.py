from fastapi import Depends, HTTPException, Header
from typing import Optional
from .jwt_handler import decode_token
from models.user import get_user_by_id


async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


async def optional_user(authorization: str = Header(None)) -> Optional[dict]:
    """Returns user dict if valid token, None otherwise. Does NOT raise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return None
        user = get_user_by_id(payload["sub"])
        return {"id": user["id"], "email": user["email"], "name": user["name"]} if user else None
    except Exception:
        return None
