"""
Time tracking service.

Live timer pattern:
  POST /time/start   → creates entry with end_time=None
  PUT  /time/stop/id → sets end_time, computes duration in seconds

Manual entry:
  POST /time/manual  → creates a complete entry in one request

Business rules:
  - Only freelancers and admins can track time.
  - A freelancer can only have one running timer at a time.
  - end_time must always be after start_time.
  - Freelancers can only edit their own entries; admins can edit any.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.time_entry import TimeEntryStart, TimeEntryStop, TimeEntryManual, TimeEntryUpdate
from app.services.task_service import get_task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, entry_id: int) -> TimeEntry:
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found.")
    return entry


def _assert_ownership(entry: TimeEntry, current_user: User) -> None:
    if not current_user.has_role("admin") and entry.freelancer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this time entry.")


def _assert_can_track(current_user: User) -> None:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot track time.")


# ── Queries ───────────────────────────────────────────────────────────────────

def list_entries(
    db: Session,
    current_user: User,
    task_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[TimeEntry]:
    q = db.query(TimeEntry)
    if not current_user.has_role("admin"):
        q = q.filter(TimeEntry.freelancer_id == current_user.id)
    if task_id:
        q = q.filter(TimeEntry.task_id == task_id)
    return q.order_by(TimeEntry.start_time.desc()).offset(skip).limit(limit).all()


def get_running_timer(db: Session, current_user: User) -> Optional[TimeEntry]:
    """Return the currently running timer for this user, or None."""
    return db.query(TimeEntry).filter(
        TimeEntry.freelancer_id == current_user.id,
        TimeEntry.end_time == None,  # noqa: E711
    ).first()


# ── Timer actions ─────────────────────────────────────────────────────────────

def start_timer(db: Session, data: TimeEntryStart, current_user: User) -> TimeEntry:
    """
    Start a live timer.
    Raises 409 if a timer is already running — only one at a time allowed.
    """
    _assert_can_track(current_user)

    running = get_running_timer(db, current_user)
    if running:
        raise HTTPException(
            status_code=409,
            detail=f"You already have a running timer (id={running.id}). Stop it before starting a new one.",
        )

    # Validate task access
    get_task(db, data.task_id, current_user)

    entry = TimeEntry(
        task_id=data.task_id,
        freelancer_id=current_user.id,
        start_time=data.start_time,
        description=data.description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def stop_timer(db: Session, entry_id: int, data: TimeEntryStop, current_user: User) -> TimeEntry:
    """Stop a running timer and compute its duration."""
    _assert_can_track(current_user)
    entry = _get_or_404(db, entry_id)
    _assert_ownership(entry, current_user)

    if entry.end_time is not None:
        raise HTTPException(status_code=400, detail="This timer has already been stopped.")

    if data.end_time <= entry.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time.")

    entry.end_time = data.end_time
    entry.duration = (data.end_time - entry.start_time).total_seconds()
    db.commit()
    db.refresh(entry)
    return entry


def create_manual_entry(db: Session, data: TimeEntryManual, current_user: User) -> TimeEntry:
    """Log a complete block of work time without a live timer."""
    _assert_can_track(current_user)
    get_task(db, data.task_id, current_user)

    duration = (data.end_time - data.start_time).total_seconds()
    entry = TimeEntry(
        task_id=data.task_id,
        freelancer_id=current_user.id,
        start_time=data.start_time,
        end_time=data.end_time,
        duration=duration,
        description=data.description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: int, data: TimeEntryUpdate, current_user: User) -> TimeEntry:
    """Edit an existing time entry. Recomputes duration if timestamps changed."""
    _assert_can_track(current_user)
    entry = _get_or_404(db, entry_id)
    _assert_ownership(entry, current_user)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)

    # Recompute duration whenever both timestamps are present
    if entry.start_time and entry.end_time:
        if entry.end_time <= entry.start_time:
            raise HTTPException(status_code=400, detail="end_time must be after start_time.")
        entry.duration = (entry.end_time - entry.start_time).total_seconds()

    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int, current_user: User) -> None:
    _assert_can_track(current_user)
    entry = _get_or_404(db, entry_id)
    _assert_ownership(entry, current_user)
    db.delete(entry)
    db.commit()