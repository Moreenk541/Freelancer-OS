"""
User routes — /api/v1/users
 
Own profile (any authenticated user):
  GET    /me                        Fetch own profile
  PATCH  /me                        Update own profile fields
  POST   /me/password               Change own password
 
Admin only:
  GET    /                          List all users (filterable by role)
  GET    /{user_id}                 Get any user by ID
  POST   /{user_id}/roles           Assign a role to a user
  DELETE /{user_id}/roles/{role}    Remove a role from a user
  PATCH  /{user_id}/deactivate      Soft-delete a user
  PATCH  /{user_id}/reactivate      Restore a deactivated user
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status,Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user,admin_required
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import (
    AssignRoleSchema,
    PasswordChange,
    
    UserOut,
    UserProfileOut,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Get own profile",
)

def get_me(current_user: User = Depends(get_current_user)):
    return current_user 

@router.patch(
    "/me",
    response_model=UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Update own profile",
    responses={
        401:{"description":"Not authenticated"},
    }
)
def update_me(
    data:UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)   
):
    return user_service.update_profile(db, current_user.id, data)

@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change own password",
    responses={
        400:{"description":"Validation error (e.g. wrong current password)"},
        401:{"description":"Not authenticated"},
    }
)
def change_password(
    data:PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service.change_password(db, current_user.id, data)



# Admin-only endpoints would go here, protected by admin_required dependency

@router.get(
    "/",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
    summary="List all users (admin only)",
    dependencies=[Depends(admin_required)],
    responses={
        401:{"description":"Not authenticated"},
        403:{"description":"Not an admin"},
    }
)

def list_users(
    role:Optional[str] =Query(
        None,
        description="Filter by role name : admin | freelancer |client",
    ),
    skip:  int = Query(0,  ge=0,   description="Pagination offset"),
    limit: int = Query(50, le=200, description="Max records to return"),
    _: User = Depends(admin_required),
    db: Session = Depends(get_db),

):
    return user_service.list_users(db, role_filter=role, skip=skip, limit=limit)

@router.get(
    "/{user_id}",
    response_model =UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Get any user by ID (admin only)",
    responses={
        403: {"description": "Admin role required"},
        404: {"description": "User not found"},
    }
)

def get_user(
    user_id :int,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return user_service.get_user(db, user_id)


@router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assign a role to a user (admin only)",
    responses={
        403: {"description": "Admin role required"},
        404: {"description": "User or role not found"},
    }
)

def assign_role(
    user_id: int,
    data: AssignRoleSchema,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    user_service.assign_role(db, user_id, data.role_name)



@router.delete(
    "/{user.id}/roles/{role_name}",
    response_model =UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Remove a role from a user (admin only)",
    responses={
        400: {"description": "Cannot remove the user's only role"},
        403: {"description": "Admin role required"},
        404: {"description": "User does not have this role"},
    },
)

def remove_role(
   user_id: int,
    role_name: str,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db), 
):
    return user_service.remove_role(db, user_id, role_name)

@router.patch(
     "/{user_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a user account [admin]",
    responses={
        400: {"description": "Cannot deactivate your own account"},
        403: {"description": "Admin role required"},
        404: {"description": "User not found"},
    },
)
def deactivate_user(
    user_id: int,
    current_admin: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
      user_service.deactivate_user(db, user_id, requesting_admin_id=current_admin.id)



@router.patch(
    "/{user_id}/reactivate",
    response_model=UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Reactivate a deactivated user [admin]",
    responses={
        403: {"description": "Admin role required"},
        404: {"description": "User not found"},
    },
)
def reactivate_user(
    user_id: int,
    _: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    """Restore a previously deactivated account. The user can log in again immediately."""
    return user_service.reactivate_user(db, user_id)
 