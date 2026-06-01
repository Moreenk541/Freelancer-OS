"""
Client service — CRUD scoped to the owning freelancer.

Business rules:
  - A freelancer can only see and manage their own clients.
  - Admins can see all clients.
  - Clients (portal users) cannot access this service.
"""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, client_id: int) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return client


def _assert_ownership(client: Client, current_user: User) -> None:
    """Admins bypass the ownership check; freelancers can only touch their own clients."""
    if not current_user.has_role("admin") and client.freelancer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this client.")


# ── CRUD ─────────────────────────────────────────────────────────────────────

def list_clients(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
) -> List[Client]:
    q = db.query(Client)
    if not current_user.has_role("admin"):
        q = q.filter(Client.freelancer_id == current_user.id)
    return q.order_by(Client.created_at.desc()).offset(skip).limit(limit).all()


def get_client(db: Session, client_id: int, current_user: User) -> Client:
    client = _get_or_404(db, client_id)
    _assert_ownership(client, current_user)
    return client


def create_client(db: Session, data: ClientCreate, current_user: User) -> Client:
    client = Client(
        **data.model_dump(),
        freelancer_id=current_user.id,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(
    db: Session,
    client_id: int,
    data: ClientUpdate,
    current_user: User,
) -> Client:
    client = get_client(db, client_id, current_user)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int, current_user: User) -> None:
    """
    Hard delete. Cascades to projects → tasks → time_entries and invoices
    via the database foreign key constraints.
    """
    client = get_client(db, client_id, current_user)
    db.delete(client)
    db.commit()