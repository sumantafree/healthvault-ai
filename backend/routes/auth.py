"""
HealthVault AI — Auth Routes
Handles user profile sync post-Supabase login.

Flow:
  1. Frontend authenticates with Supabase (Google OAuth / email)
  2. Frontend receives a Supabase JWT
  3. Frontend calls POST /auth/me to sync user with our DB
  4. All subsequent requests include the JWT in Authorization: Bearer
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser, get_current_user
from models.user import User
from schemas.user import UserPublic, UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/me", response_model=UserPublic, summary="Sync authenticated user to DB")
async def sync_user(current_user: CurrentUser) -> User:
    """
    Called by the frontend immediately after Supabase login.
    Auto-creates the user row if this is their first visit.
    Returns the user's profile.
    """
    return current_user


@router.get("/me", response_model=UserPublic, summary="Get current user profile")
async def get_me(current_user: CurrentUser) -> User:
    """Returns the authenticated user's public profile."""
    return current_user


@router.patch("/me", response_model=UserPublic, summary="Update current user profile")
async def update_me(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update mutable fields of the current user's profile."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=204, summary="Deactivate current user account")
async def deactivate_me(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-deletes the user account (sets is_active=False).
    The Supabase account is NOT deleted — handle that separately if needed.
    """
    current_user.is_active = False
    db.add(current_user)
    await db.commit()
