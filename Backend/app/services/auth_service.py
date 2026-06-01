"Register"
"Login"
"token refresh"

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.security import (create_access_token,
                               create_refresh_token,
                               hash_password,
                                verify_password,
                                 SECRET_KEY,
                                    ALGORITHM
                                )

from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterSchema, LoginSchema, TokenResponse, TokenPair


def register (db:Session,data:RegisterSchema) -> TokenResponse:
    # Check if email already exists
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code = 408, detail="Email already registered")
    
    freelancer_role = db.query(Role).filter(Role.name == "freelancer").first()
    if not freelancer_role:
        raise HTTPException(status_code=500, detail="Freelancer role not found in database.")
    

    # Create new user
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        roles=[freelancer_role]
    )
    db.add(user)
    db.commit()
    db.refresh(user)


    token =create_access_token({"sub":str(user.id), "roles": user.role_names})
    return TokenResponse(access_token=token)
      


def login(db:Session, data:LoginSchema) -> TokenPair:
    user =db.query(User.filter(User.email == data.email)).first()

    if not user or not verify_password(data.password,user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated")


    payload = {"sub": str(user.id), "roles": user.role_names}
    return TokenPair(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload)
    )
    

def refresh(db: Session, refresh_token: str) -> TokenResponse:
   
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token.")
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
 
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists.")
 
    token = create_access_token({"sub": str(user.id), "roles": user.role_names})
    return TokenResponse(access_token=token)
 