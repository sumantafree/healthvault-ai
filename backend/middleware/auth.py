"""
HealthVault AI — Auth Middleware
Validates Supabase JWT tokens and injects the current user into requests.
"""
import uuid
from typing import Annotated, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User

security = HTTPBearer()


# ── JWT Verification ─────────────────────────────────────────────────────────

def _decode_supabase_jwt(token: str) -> dict:
    """
    Verify and decode a Supabase-issued JWT.
    Supabase uses HS256 with the project JWT secret.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase doesn't always set aud
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
    payload = _decode_supabase_jwt(credentials.credentials)
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
    payload = _decode_supabase_jwt(credentials.credentials)
    return await get_or_create_user(payload, db)


# ── Type aliases (convenience) ────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
