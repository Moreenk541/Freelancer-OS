"""
Project service.

Business rules:
  - Freelancers can only manage projects they own.
  - Clients can view their own projects and set status → approved + feedback.
  - Admins have full access.
"""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.project import Project, ProjectStatus
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectDetail


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def _assert_access(project: Project, current_user: User) -> None:
    """
    Admins: full access.
    Freelancers: only their own projects.
    Clients: only projects linked to their client record.
    """
    if current_user.has_role("admin"):
        return

    if current_user.has_role("freelancer") and project.freelancer_id == current_user.id:
        return

    if current_user.has_role("client"):
        # Client portal users are linked via clients.user_id
        if project.client and project.client.user_id == current_user.id:
            return

    raise HTTPException(status_code=403, detail="You do not have access to this project.")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_projects(
    db: Session,
    current_user: User,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Project]:
    q = db.query(Project)

    if current_user.has_role("admin"):
        pass  # sees everything
    elif current_user.has_role("freelancer"):
        q = q.filter(Project.freelancer_id == current_user.id)
    elif current_user.has_role("client"):
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            return []
        q = q.filter(Project.client_id == client.id)

    if status_filter:
        q = q.filter(Project.status == status_filter)

    return q.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()


def get_project(db: Session, project_id: int, current_user: User) -> Project:
    project = _get_or_404(db, project_id)
    _assert_access(project, current_user)
    return project


def get_project_detail(db: Session, project_id: int, current_user: User) -> ProjectDetail:
    """Return the project with nested client info and task progress counters."""
    project = get_project(db, project_id, current_user)
    tasks   = project.tasks.all()

    return ProjectDetail(
        **project.__dict__,
        client=project.client,
        task_count=len(tasks),
        completed_tasks=sum(1 for t in tasks if t.status == TaskStatus.DONE),
    )


def create_project(db: Session, data: ProjectCreate, current_user: User) -> Project:
    # Verify the client exists and belongs to this freelancer
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    if not current_user.has_role("admin") and client.freelancer_id != current_user.id:
        raise HTTPException(status_code=403, detail="That client does not belong to you.")

    project = Project(
        **data.model_dump(),
        freelancer_id=current_user.id,
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session,
    project_id: int,
    data: ProjectUpdate,
    current_user: User,
) -> Project:
    project = get_project(db, project_id, current_user)

    # Clients can only approve and leave feedback
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        allowed_fields = {"status", "client_feedback"}
        updates = {k: v for k, v in data.model_dump(exclude_none=True).items()
                   if k in allowed_fields}
        if "status" in updates and updates["status"] != ProjectStatus.APPROVED:
            raise HTTPException(
                status_code=403,
                detail="Clients can only set project status to 'approved'.",
            )
    else:
        updates = data.model_dump(exclude_none=True)

    for field, value in updates.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, current_user: User) -> None:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot delete projects.")
    project = get_project(db, project_id, current_user)
    db.delete(project)