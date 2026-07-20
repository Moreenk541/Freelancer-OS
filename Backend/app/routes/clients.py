
"""
Client routes — /api/v1/clients
 
GET    /              List own clients (admin sees all)
POST   /              Create a new client
GET    /{id}          Get a single client
PATCH  /{id}          Update client details
DELETE /{id}          Delete a client (cascades to projects and invoices)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException,query,status
from sqlalchemy.orm import Session

from app.core.dependencies import freelancer_required
from app.core.constants import Pagination
from database.database import get_db
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/",response_model=List[ClientOut])

def list_clients(
    skip:  int = Query(Pagination.DEFAULT_SKIP,  ge=0, description="Pagination offset"),
    limit: int = Query(Pagination.DEFAULT_LIMIT, le=Pagination.MAX_LIMIT, description="Max records"),
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> List[ClientOut]:
    return client_service.list_clients(db, current_user, skip=skip, limit=limit)

@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)

def create_client(
    data: ClientCreate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) ->ClientOut:
    
    return client_service.create_client(db, current_user, data)

@router.get("/{client_id}",response_model=ClientOut)
def get_client(
    id: int,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> ClientOut:
    return client_service.get_client(db, current_user, id)

@router.patch("/{client_id}",response_model=ClientOut)
def update_client(
    id: int,
    data: ClientUpdate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> ClientOut:
    return client_service.update_client(db, current_user, id, data)

@router.delete("/{client_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db)
) -> None:
    return client_service.delete_client(db, current_user, client_id)

