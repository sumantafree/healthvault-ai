"""
HealthVault AI — Auth Middleware
Validates Supabase JWT tokens and injects the current user into requests.

Tokens are validated by calling Supabase's `/auth/v1/user` endpoint, which
works with any signing algorithm (HS256 legacy projects + ES256/RS256
asymmetric-key projects). This avoids having to ship a JWT secret to the
backend or implement JWKS rotation locally.
"""
import uuid
from typing import Annotated, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User

security = HTTPBearer()


# ── JWT Verification (via Supabase auth API) ─────────────────────────────────

async def _verify_supabase_jwt(token: str) -> dict:
    """
    Verify a Supabase-issued JWT by calling Supabase's GoTrue /user endpoint.
    Returns the user payload (with `id`, `email`, `user_metadata`, etc.) on
    success, raises 401 on any failure. Works with HS256, ES256, or RS256.
    """
    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured on the server.",
        )

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        # GoTrue requires the apikey header; the anon/service-role key works.
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY or "",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as http:
            r = await http.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Supabase auth: {e}",
        )

    if r.status_code != 200:
        # Surface the real reason (expired token, invalid sig, etc.)
        try:
            msg = r.json().get("msg") or r.json().get("error_description") or r.text
        except Exception:
            msg = r.text
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {msg}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = r.json()
    # Normalize to look like the JWT payload our downstream code expects.
    return {
        "sub": user["id"],
        "email": user.get("email", ""),
        "user_metadata": user.get("user_metadata", {}) or {},
    }


# ── User Resolution ───────────────────────────────────────────────────────────

async def get_or_create_user(
    payload: dict,
    db: AsyncSession,
) -> User:
    """
    Resolve the DB user from the JWT sub claim.
    Auto-creates the user row on first login (Supabase handles the actual auth).
    """
    supabase_uid = uuid.UUID(payload["sub"])
    email = payload.get("email", "")

    result = await db.execute(
        select(User).where(User.supabase_uid == supabase_uid)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # First-time login — create the user record
        user = User(
            supabase_uid=supabase_uid,
            email=email,
            full_name=payload.get("user_metadata", {}).get("full_name"),
            avatar_url=payload.get("user_metadata", {}).get("avatar_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    return user


# ── FastAPI Dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Primary auth dependency — validates JWT and returns the DB user."""
    payload = await _verify_supabase_jwt(credentials.credentials)
    return await get_or_create_user(payload, db)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional auth — returns None instead of raising if no token provided."""
    if credentials is None:
        return None
    payload = await _verify_supabase_jwt(credentials.credentials)
    return await get_or_create_user(payload, db)


# ── Type aliases (convenience) ────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
