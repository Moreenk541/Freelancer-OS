"""
Client schemas.
 
ClientCreate — request body for POST /clients
ClientUpdate — request body for PATCH /clients/{id}  (all optional)
ClientOut    — response model
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr 
    company: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    phone: Optional[str] = Field(None, max_length=20)


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    company: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    phone: Optional[str] = Field(None, max_length=20)

class ClientOut(BaseModel):
    id:int 
    freelancer_id: int
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


    model_config = {
        "from_attributes": True
    }



