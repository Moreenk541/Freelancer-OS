"""
File service — upload, list, delete project attachments.

Files are stored on local disk at UPLOAD_DIR/{project_id}/{uuid}{ext}.
For production S3/GCS, only the save_file() storage section needs swapping.

Business rules:
  - Any role with project access can download/view files.
  - Only the uploader or an admin can delete a file.
  - File size is capped at MAX_UPLOAD_SIZE_MB.
"""
import uuid
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.user import User
from app.services.project_service import get_project


# ── Storage helpers ───────────────────────────────────────────────────────────

def _project_upload_dir(project_id: int) -> Path:
    path = Path(settings.UPLOAD_DIR) / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_files(db: Session, project_id: int, current_user: User) -> List[File]:
    get_project(db, project_id, current_user)
    return (
        db.query(File)
        .filter(File.project_id == project_id)
        .order_by(File.created_at.desc())
        .all()
    )


async def upload_file(
    db: Session,
    project_id: int,
    upload: UploadFile,
    current_user: User,
) -> File:
    # Verify project access
    get_project(db, project_id, current_user)

    # Read and size-check
    contents = await upload.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    # Build a collision-proof stored filename
    ext         = Path(upload.filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest        = _project_upload_dir(project_id) / stored_name

    with open(dest, "wb") as fh:
        fh.write(contents)

    file_record = File(
        project_id=project_id,
        uploaded_by=current_user.id,
        file_name=upload.filename,
        stored_name=stored_name,
        file_url=f"/uploads/{project_id}/{stored_name}",
        mime_type=upload.content_type,
        size_bytes=len(contents),
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def delete_file(db: Session, file_id: int, current_user: User) -> None:
    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    # Only uploader or admin may delete
    if not current_user.has_role("admin") and file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete files you uploaded.")

    # Remove from disk (best-effort — don't fail if file is already gone)
    disk_path = (
        Path(settings.UPLOAD_DIR) / str(file_record.project_id) / file_record.stored_name
    )
    if disk_path.exists():
        disk_path.unlink()

    db.delete(file_record)
    db.commit()