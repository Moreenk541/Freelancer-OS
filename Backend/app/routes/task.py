
"""
Task routes  
 
GET    /project/{project_id}   List all tasks for a project
POST   /                       Create a task inside a project
GET    /{id}                   Get a single task
PATCH  /{id}                   Update fields or advance status
DELETE /{id}                   Delete task and all its time entries
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.constants import Pagination, TaskStatus as TS
from app.core.dependencies import freelancer_required, get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/" ,response_model= List[TaskOut]) 
def list_tasks(
    project_id:int,
    status_filter: Optinal[str] =query(
        None,
        alias="status",
        description=f"Filter by status: {' | '.join(TS.ALL)}",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ) -> List[TaskOut]:
    return task_service.list_tasks(db, current_user, project_id, status_filter=status_filter)

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> TaskOut:
    return task_service.create_task(db, current_user, data)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    return task_service.get_task(db, task_id, current_user)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    return task_service.update_task(db, task_id, current_user, data)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    return task_service.delete_task(db, task_id, current_user)