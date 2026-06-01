"""
User service — profile management and admin user operations.
"""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserUpdate, PasswordChange


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ── Profile ───────────────────────────────────────────────────────────────────

def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    """Update the current user's own profile fields."""
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    """
    Change the current user's password.
    Requires the existing password to prevent CSRF / session-hijack abuse.
    """
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.hashed_password = hash_password(data.new_password)
    db.commit()


# ── Admin ─────────────────────────────────────────────────────────────────────

def list_users(
    db: Session,
    role_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[User]:
    """Return all users, optionally filtered by role name."""
    q = db.query(User)
    if role_filter:
        q = q.join(User.roles).filter(Role.name == role_filter)
    return q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int) -> User:
    return _get_or_404(db, user_id)


def assign_role(db: Session, user_id: int, role_name: str) -> User:
    """
    Add a role to a user.
    Idempotent — silently succeeds if the user already has the role.
    Raises 404 if the role name does not exist.
    """
    user = _get_or_404(db, user_id)
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_name}' does not exist. Valid roles: admin, freelancer, client.",
        )
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
    return user


def remove_role(db: Session, user_id: int, role_name: str) -> User:
    """
    Remove a role from a user.
    Raises 400 if it would leave the user with no roles.
    Raises 404 if the user does not have the role.
    """
    user = _get_or_404(db, user_id)
    role = next((r for r in user.roles if r.name == role_name), None)
    if not role:
        raise HTTPException(
            status_code=404,
            detail=f"User does not have role '{role_name}'.",
        )
    if len(user.roles) == 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the user's only role. Assign another role first.",
        )
    user.roles.remove(role)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int, requesting_admin_id: int) -> None:
    """
    Soft-delete a user by setting is_active=False.
    Raises 400 if an admin tries to deactivate themselves.
    """
    if user_id == requesting_admin_id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")
    user = _get_or_404(db, user_id)
    user.is_active = False
    db.commit()


def reactivate_user(db: Session, user_id: int) -> User:
    """Restore a previously deactivated user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user