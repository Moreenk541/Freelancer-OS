from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.database import get_db

router = APIRouter(prefix="/clients", tags="Clients")

@router.post("/create_client")
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")