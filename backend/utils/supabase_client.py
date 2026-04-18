"""
HealthVault AI — Supabase Client
Provides a singleton Supabase client for storage and admin operations.
"""
from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache()
def get_supabase() -> Client:
    """Returns a Supabase client using the service role key (server-side only)."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )


@lru_cache()
def get_supabase_anon() -> Client:
    """Returns a Supabase client using the anon/public key."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )
