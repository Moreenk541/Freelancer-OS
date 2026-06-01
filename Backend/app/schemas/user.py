"""
User / profile schemas.
 
RoleOut         — role object in responses
UserOut         — base user response (id, name, email, roles)
UserProfileOut  — full profile including freelancer fields
UserUpdate      — editable profile fields (all optional)
PasswordChange  — current + new password
AssignRoleSchema — admin: add a role to a user by name
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field ,field_validator

class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    roles: List[RoleOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}

class UserProfileOut(UserOut):    
    bio: Optional[str] = None
    skills: Optional[str] = None
    hourly_rate: Optional[float] = None
    portfolio_url: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    
    bio: Optional[str] = Field(None, max_length=1000)
    skills: Optional[str] = Field(None, max_length=500)
    hourly_rate: Optional[float] = Field(None, gt=0)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)

 
# class PasswordChange(BaseModel):
#     """POST /users/me/password — requires current password to prevent CSRF abuse."""
#     current_password: str
#     new_password:     str = Field(..., min_length=8, max_length=128)
 
#     @field_validator("new_password")
#     @classmethod
#     def new_password_strength(cls, v: str) -> str:
#         if not any(c.isdigit() for c in v):
#             raise ValueError("New password must contain at least one digit.")
#         if not any(c.isupper() for c in v):
#             raise ValueError("New password must contain at least one uppercase letter.")
#         return v
 
 
# class AssignRoleSchema(BaseModel):
#     """
#     POST /users/{id}/roles — admin assigns a role by name.
#     Valid values: 'admin', 'freelancer', 'client'.
#     """
#     role_name: str = Field(..., min_length=1, max_length=50)
 