
"""
Time tracking routes  ·  /api/v1/time
 
─────────────────────────────────────────────────────────────────────────
Live timer flow  (for tracking work as it happens)
─────────────────────────────────────────────────────────────────────────
  POST  /start         Create entry with start_time, end_time = null
  PUT   /stop/{id}     Set end_time, compute duration in seconds
 
─────────────────────────────────────────────────────────────────────────
Manual entry flow  (for logging past work)
─────────────────────────────────────────────────────────────────────────
  POST  /manual        Supply both start_time and end_time in one request
 
─────────────────────────────────────────────────────────────────────────
General
─────────────────────────────────────────────────────────────────────────
  GET   /              List entries (filterable by task_id)
  GET   /running       The currently running timer, or null
  PATCH /{id}          Correct timestamps or description
  DELETE /{id}         Delete an entry
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import Pagination
from app.core.dependencies import get_db, freelancer_required
from app.models.user import User
from app.schemas.time_entry import (
    TimeEntryManual,
    TimeEntryOut,
    TimeEntryStart,
    TimeEntryStop,
    TimeEntryUpdate,
)
from app.services import time_service

router = APIRouter(prefix="/time", tags=["Time Tracking"])

@router.get("/", response_model=List[TimeEntryOut])
def list_entries(
    task_id: Optional[int] = Query(None, description="Filter by specific task_id"),
    skip:    int = Query(Pagination.DEFAULT_SKIP,    ge=0,   description="Pagination offset"),
    limit:   int = Query(100, le=500, description="Max records to return"),
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> List[TimeEntryOut]:
   return time_service.list_entries(db, current_user, task_id=task_id, skip=skip, limit=limit)

@router.get("/running", response_model=Optional[TimeEntryOut])
def get_running_timer(
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> Optional[TimeEntryOut]:
    return time_service.get_running_timer(db, current_user
    )


@router.post("/start", response_model=TimeEntryOut)
def start_timer(
    data: TimeEntryStart,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> TimeEntryOut:
    return time_service.start_timer(db, current_user, data)


@router.put("/stop/{entry_id}", response_model=TimeEntryOut)
def stop_timer(
    entry_id: int,
    data: TimeEntryStop,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> TimeEntryOut:
    return time_service.stop_timer(db, current_user, entry_id, data)


@router.post("/manual", response_model=TimeEntryOut)
def manual_entry(
    data: TimeEntryManual,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> TimeEntryOut:
  
    return time_service.create_manual_entry(db, data, current_user)
 
 
@router.patch(
    "/{entry_id}",
    response_model=TimeEntryOut,
    
)
def update_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> TimeEntryOut:
   
    return time_service.update_entry(db, entry_id, data, current_user)
 
 
@router.delete(
    "/{entry_id}",

)
def delete_entry(
    entry_id: int,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> None:

    time_service.delete_entry(db, entry_id, current_user)
 
    