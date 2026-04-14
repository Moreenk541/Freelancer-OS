from datetime import datetime
from typing import List

from sqlalchemy import String,DateTime, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.database.database import Base
from app.models.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key =True)
    name: Mapped[str] = mapped_column(String(255),nullable=False)
    email: Mapped[str] = mapped_column(String(255),unique=True,nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255),nullable=False)
    role: Mapped[UserRole] = mapped_column(nullable = False , default = UserRole.FREELANCER)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default = func.now(), nullable =False)

def __repr__(self) -> str :
    return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
             