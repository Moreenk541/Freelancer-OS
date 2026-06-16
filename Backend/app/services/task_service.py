"""
Task service.

Business rules:
  - Tasks belong to a project; project access rules cascade down to tasks.
  - Only freelancers and admins can create, update, or delete tasks.
  - Completing a task (status → done) auto-records completed_at.
  - Reopening a task clears completed_at.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import get_project


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


def _assert_project_access(db: Session, task: Task, current_user: User) -> None:
    """Reuse project-level access check to guard task access."""
    get_project(db, task.project_id, current_user)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_tasks(
    db: Session,
    project_id: int,
    current_user: User,
    status_filter: Optional[str] = None,
) -> List[Task]:
    # Validate project access first
    get_project(db, project_id, current_user)

    q = db.query(Task).filter(Task.project_id == project_id)
    if status_filter:
        q = q.filter(Task.status == status_filter)
    return q.order_by(Task.created_at.desc()).all()


def get_task(db: Session, task_id: int, current_user: User) -> Task:
    task = _get_or_404(db, task_id)
    _assert_project_access(db, task, current_user)
    return task


def create_task(db: Session, data: TaskCreate, current_user: User) -> Task:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot create tasks.")

    # Validate project access
    get_project(db, data.project_id, current_user)

    task = Task(**data.model_dump(), status=TaskStatus.TODO)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate, current_user: User) -> Task:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot edit tasks.")

    task    = get_task(db, task_id, current_user)
    updates = data.model_dump(exclude_none=True)

    # Auto-manage completed_at based on status transitions
    new_status = updates.get("status")
    if new_status == TaskStatus.DONE and task.status != TaskStatus.DONE:
        task.completed_at = datetime.now(timezone.utc)
    elif new_status and new_status != TaskStatus.DONE:
        task.completed_at = None

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, current_user: User) -> None:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot delete tasks.")
    task = get_task(db, task_id, current_user)
    db.delete(task)
    db.commit()