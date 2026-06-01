
"""
Project schemas.
 
ProjectCreate — freelancer creates a project for a client
ProjectUpdate — freelancer edits; client can only set status=approved + feedback
ProjectOut    — standard list/create response
ProjectDetail — single project view with nested client + task counts
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.client import ClientOut
from app.models import ProjectStatus

class ProjectCreate(BaseModel):
    client_id : int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    deadline: Optional[datetime] = None 
    budget: Optional[float] = Field(None, gt=0)


class ProjectUpdate(BaseModel):
    title:           Optional[str]           = Field(None, min_length=1, max_length=200)
    description:     Optional[str]           = Field(None, max_length=5000)
    status:          Optional[ProjectStatus] = None
    deadline:        Optional[datetime]          = None
    budget:          Optional[int]           = Field(None, ge=0)
    client_feedback: Optional[str]           = Field(None, max_length=2000)
 
class ProjectOut(BaseModel): 
    id:              int
    freelancer_id:   int
    client_id:       int
    title:           str
    description:     Optional[str]    = None
    status:          ProjectStatus
    deadline:        Optional[datetime]   = None
    budget:          Optional[int]    = None
    client_feedback: Optional[str]    = None
    created_at:      datetime
 
    model_config = {"from_attributes": True}

class ProjectDetail(ProjectOut):
    client: ClientOut
    task_count: int
    completed_tasks: int

    model_config = {"from_attributes": True}