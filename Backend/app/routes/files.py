"""
File routes  ·  /api/v1/files

GET    /project/{project_id}   List files attached to a project
POST   /project/{project_id}   Upload a file to a project
DELETE /{file_id}              Delete a file

Access rules:
    List / Upload — any user with access to the parent project
    Delete        — uploader or admin only

Storage:
    Files land on disk at  UPLOAD_DIR/{project_id}/{uuid}{ext}
    UUID-based filenames prevent path traversal and name collisions.
    Swap the storage backend in file_service.upload_file() for S3/GCS.
"""
from typing import List

from fastapi import APIRouter, Depends, File as FastAPIFile, UploadFile, status
from sqlalchemy.orm import Session

from app.core.constants import ErrorMessage, FileUpload
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.file import FileOut
from app.services import file_service

router = APIRouter(prefix="/files", tags=["Files"])

# Build a human-readable extension string once for use in docstrings
_ALLOWED_EXT = "  ".join(FileUpload.ALLOWED_EXTENSIONS)


@router.get(
    "/project/{project_id}",
    response_model=List[FileOut],
    status_code=status.HTTP_200_OK,
    summary="List files for a project",
    response_description="All files attached to the project, newest first",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": ErrorMessage.NOT_YOUR_PROJECT},
        404: {"description": ErrorMessage.PROJECT_NOT_FOUND},
    },
)
def list_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[FileOut]:
    """
    Return all files attached to a project, ordered newest first.

    Access follows the parent project's ownership rules:
    - **Freelancer** — must own the project
    - **Client** — project must be linked to their client record
    - **Admin** — any project
    """
    return file_service.list_files(db, project_id, current_user)


@router.post(
    "/project/{project_id}",
    response_model=FileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file to a project",
    response_description="File metadata record including the download URL",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": ErrorMessage.NOT_YOUR_PROJECT},
        404: {"description": ErrorMessage.PROJECT_NOT_FOUND},
        413: {"description": ErrorMessage.FILE_TOO_LARGE},
    },
)
async def upload_file(
    project_id: int,
    file: UploadFile = FastAPIFile(
        ...,
        description=(
            f"File to upload. "
            f"Max size is controlled by the MAX_UPLOAD_SIZE_MB environment variable "
            f"(default: 10 MB). "
            f"Supported extensions: {_ALLOWED_EXT}"
        ),
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileOut:
    """
    Upload a file and attach it to a project.

    **What gets stored:**
    - `file_name` — the original filename sent by the client (for display)
    - `stored_name` — a UUID-based name used on disk (internal, prevents collisions)
    - `file_url` — the URL to download or preview the file
    - `mime_type` — detected from the upload content-type header
    - `size_bytes` — byte count of the uploaded file

    **Limits:**
    - Max file size: set by `MAX_UPLOAD_SIZE_MB` env var (default 10 MB)
    - Allowed types: images, PDFs, Word/Excel documents, plain text, CSV, ZIP

    **Downloading:** use the `file_url` value from the response.
    Files are served from `/uploads/{project_id}/{stored_name}`.
    """
    return await file_service.upload_file(db, project_id, file, current_user)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": ErrorMessage.NOT_YOUR_FILE},
        404: {"description": ErrorMessage.FILE_NOT_FOUND},
    },
)
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a file record and remove it from disk.

    **Permission:** only the user who originally uploaded the file, or an admin.
    Other project members can view and download files but cannot delete them.

    If the file has already been removed from disk (e.g. manual cleanup),
    the database record is still deleted cleanly without raising an error.
    """
    file_service.delete_file(db, file_id, current_user)