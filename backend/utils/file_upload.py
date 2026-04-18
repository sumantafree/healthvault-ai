"""
HealthVault AI — File Upload Utility
Handles validation and upload to Supabase Storage or AWS S3.
"""
import hashlib
import io
import uuid
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, UploadFile, status

from config import settings
from utils.supabase_client import get_supabase


# ── Validation ────────────────────────────────────────────────────────────────

async def validate_upload(file: UploadFile) -> bytes:
    """
    Read and validate an uploaded file.
    Returns the raw bytes if valid; raises HTTPException otherwise.
    """
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' is not allowed. "
                   f"Accepted: {', '.join(settings.ALLOWED_MIME_TYPES)}",
        )

    contents = await file.read()

    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    return contents


# ── Storage Upload ─────────────────────────────────────────────────────────────

async def upload_file_to_supabase(
    contents: bytes,
    original_filename: str,
    bucket: str,
    user_id: uuid.UUID,
    folder: str = "",
) -> str:
    """
    Uploads a file to Supabase Storage.
    Returns the public URL.

    Path pattern: {user_id}/{folder}/{uuid}_{filename}
    """
    ext = Path(original_filename).suffix.lower()
    safe_name = f"{uuid.uuid4()}_{Path(original_filename).stem[:50]}{ext}"
    path = f"{user_id}/{folder}/{safe_name}".lstrip("/")

    supabase = get_supabase()

    try:
        response = supabase.storage.from_(bucket).upload(
            path=path,
            file=contents,
            file_options={"content-type": _mime_from_ext(ext)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {str(exc)}",
        )

    # Build the public URL
    url_response = supabase.storage.from_(bucket).get_public_url(path)
    return url_response


async def delete_file_from_supabase(bucket: str, file_url: str) -> None:
    """Deletes a file from Supabase Storage by its public URL."""
    supabase = get_supabase()
    # Extract path from URL: everything after /storage/v1/object/public/{bucket}/
    marker = f"/object/public/{bucket}/"
    idx = file_url.find(marker)
    if idx == -1:
        return
    path = file_url[idx + len(marker):]
    supabase.storage.from_(bucket).remove([path])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mime_from_ext(ext: str) -> str:
    mapping = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return mapping.get(ext.lower(), "application/octet-stream")


def compute_file_hash(contents: bytes) -> str:
    """SHA-256 hash of file contents — useful for dedup detection."""
    return hashlib.sha256(contents).hexdigest()
