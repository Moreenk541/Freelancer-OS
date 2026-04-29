from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.models.role import Role

router = APIRouter(prefix="/users", tags= "Users")

@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "roles": [role.name for role in current_user.roles]
    }

@router.post("/add-role")
def add_role(
    role_name : str,
    current_user : User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(role.name == role_name).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")


    if role in current_user.roles:  
        raise HTTPException(status_code=400, detail="Role already assigned")  
    
    current_user.roles.append(role)

    db.commit()
    db.refresh(current_user)

    return {"message": f"Role '{role_name}' added successfully"}


@router.post("/switch-role")
def switch_role(
    role_name: str,
    current_user:User  = Depends(get_current_user),
    db: Session = Depends(get_db)

):
    if role_name not in [role.name for role in current_user.roles]:
        raise HTTPException(status_code=400, detail="Role not assigned to the user")
    
    current_user.active_role = role_name

    db.commit()
    db.refresh(current_user)

    return {"message": f"Switched to {role_name}"}


@router.get("/admin")
def require_admin(user):
    if not any(role.name == "admin" for role in user.roles):
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/all")
def get_all_users(
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    require_admin(current_user)
    return db.query(User).all()
  
@router.posr("/{user_id}/assign-role")
def assign_role(
    user_id:int,
    role_name:str,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    require_admin(current_user)

    user = db.query(User).get(user_id)
    role=db.query(Role).filter(Role.name == role_name).first()

    if not user or role:
        raise HTTPException(status_code=404, detail="User or Role not found")
    

    if role in user.roles:
        raise HTTPException(status_code=400, detail="Role already assigned to user")
    
    user.roles.append(role)
    db.commit()
    db.refresh(user)

    return {"message": "Role assigned successfully"}
    

@router.post("/{user_id}/remove-role")    
def remove_role(
    user_id:int,
    role_name:str,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    require_admin(current_user)

    user = db.query(User).get(user_id)
    role=db.query(Role).filter(Role.name == role_name).first()

    if not user or role:
        raise HTTPException(status_code=404, detail="User or Role not found")
    

    if role not in user.roles:
        raise HTTPException(status_code=400, detail="Role not assigned to user")
    
    user.roles.remove(role)
    db.commit()
    db.refresh(user)

    return {"message": "Role removed successfully"}

@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id:int,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    require_admin(current_user)

    user = db.query(User).get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    db.refresh(user)

    return {"message": "User deactivated successfully"}


@router.patch("/{user_id}/activate")
def activate_user(
    user_id:int,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    require_admin(current_user)

    user = db.query(User).get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    db.refresh(user)

    return {"message": "User activated successfully"}

@router.post("/change-password")
def change_password(
    old_password:str,
    new_password:str,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    from app.core.security import verify_password, hash_password

    if not verify_password(old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(current_user)    
    return {"message": "Password updated successfully"}