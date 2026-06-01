
"""
Task schemas.
 
TaskCreate — add a task to a project
TaskUpdate — edit task fields or advance its status
TaskOut    — response model
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.task import TaskStatus

class TaskCreate(BaseModel):
    project_id: int
    title: str =Field(...,min_length=1,max_length=2000)
    description: Optional[str] = Field(None,max_length=5000)
    due_date: Optional[datetime] = None
    estimated_hours :Optional[float] =Field(None,ge=0)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None,min_length=1,max_length=2000)
    description: Optional[str] = Field(None,max_length=5000)
    due_date: Optional[datetime] = None
    estimated_hours :Optional[float] =Field(None,ge=0)
    status: Optional[TaskStatus] = None 

class TaskOut(BaseModel):
    id:              int
    project_id:      int
    title:           str
    description:     Optional[str]      = None
    status:          TaskStatus
    
    due_date:        Optional[date]     = None
    estimated_hours: Optional[int]      = None
    created_at:      datetime
    completed_at:    Optional[datetime] = None
 
    model_config = {"from_attributes": True}
 

