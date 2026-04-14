from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text,DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

class Client(Base):
    __tablename__ ="clients"

    id: Mapped[int] = mapped_column(primary_key = True)
    freelancer_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    name: Mapped[str] =mapped_column(String(255),nullable=False)
    email: Mapped[str] =mapped_column(String(255),nullable=False)
    company: Mapped[Optional[str]]= mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(),nullable=False)


    def __repr__(self) -> str:
        return f"<Client (id={self.id},name={self.name})>"