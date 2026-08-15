import re
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import settings

ALLOWED = {".pdf": "pdf", ".docx": "docx", ".txt": "txt", ".csv": "csv"}
MIME_BY_EXT = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream"},
}

def secure_filename(name: str) -> str:
    base = Path(name or "upload").name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return safe[:180] or "upload"

async def validate_and_save(upload: UploadFile, owner_id: str) -> tuple[str, str, int, str]:
    original = secure_filename(upload.filename or "upload")
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Unsupported file type. Allowed: PDF, DOCX, TXT, CSV")
    if upload.content_type and upload.content_type not in MIME_BY_EXT[ext]:
        raise ValueError(f"MIME type {upload.content_type!r} does not match {ext}")
    data = await upload.read(settings.max_upload_size + 1)
    if len(data) > settings.max_upload_size:
        raise ValueError("File exceeds configured upload size limit")
    if not data:
        raise ValueError("File is empty")
    user_dir = settings.upload_path / owner_id
    user_dir.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{ext}"
    path = user_dir / stored
    path.write_bytes(data)
    return str(path), ALLOWED[ext], len(data), original
