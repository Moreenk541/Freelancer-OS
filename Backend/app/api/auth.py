from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from app.database.database import get_db
from app.models.user import User
from app.models.role  import Role
from app.schemas.auth import RegisterRequest, LoginRequest,TokenResponse
from app.core.security import hash_password,verify_password,create_access_token,SECRET_KEY,ALGORITHM

router = APIRouter(prefix="/auth", tags= "Auth")

outh2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/login")

        ## Registration Endpoint
@router.post("/register", response_model= TokenResponse)
def register(data:RegisterRequest,db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email ==data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    freelancer_role = db.query(Role).filter(Role.name == "freelancer").first()

    new_user = User(
        name = data.name,
        email = data.email,
        hashed_password= hash_password(data.password),
        roles=[freelancer_role]
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})

    return {"access_token" : token}

            #   Login Endpoint
@router.post("/login", response_model= TokenResponse)
def login(data:LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    

    token = create_access_token({"sub": str(user.id)})

    return {"access_token": token, "token_type": "bearer"}

        ## Get Current User Endpoint
def get_current_user( token: str = Depends(outh2_scheme), db:Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).get(int(user_id))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    return user

def require_admin(user):
    if not any(role.name == "admin" for role in user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")