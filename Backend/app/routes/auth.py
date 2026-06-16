"""
POST/ register
POST/ login
POST/ refresh
GET/me
"""

from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginSchema,
    RefreshRequest,
    RegisterSchema,
    TokenPair,
    TokenResponse,
)

from app.schemas.user import UserProfileOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,

)

def register(data: RegisterSchema, db: Session = Depends(get_db)):
    return auth_service.register(db, data)


@router.post("/login", response_model=TokenPair)
def login(data: LoginSchema, db: Session = Depends(get_db)):
    return auth_service.login(db, data)

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh(db, data.refresh_token)

@router.get("/me", response_model=UserProfileOut)
def profile(current_user: User = Depends(get_current_user)):
    return  current_user
