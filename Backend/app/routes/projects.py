
# Project routes  ·  /api/v1/projects
 
# GET    /         List projects (role-scoped)
# POST   /         Create a project under a client
# GET    /{id}     Full detail — nested client + task progress counters
# PATCH  /{id}     Update (clients restricted to approve + feedback only)


from typing import List,Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.constants import Pagination,ProjectStatus as PS
from app.core.dependencies import freelancer_required,get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/", response_model=List[ProjectOut])

def list_projects(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description=f"Filter by status: {' | '.join(PS.ALL)}",
    ),
    skip:  int = Query(Pagination.DEFAULT_SKIP,  ge=0,  description="Pagination offset"),
    limit: int = Query(Pagination.DEFAULT_LIMIT, le=Pagination.MAX_LIMIT, description="Max records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ProjectOut]:
    
    return project_service.list_projects(db, current_user, status_filter=status_filter, skip=skip, limit=limit)

@router.post("/",response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> ProjectOut:
    
    return project_service.create_project(db, current_user, data)

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    
    return project_service.get_project(db, project_id, current_user)

@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectOut:
    
    return project_service.update_project(db, project_id, current_user, data)       

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    
    return project_service.delete_project(db, project_id, current_user)