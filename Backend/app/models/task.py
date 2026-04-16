from datetime import datetime
from typing import List, Optional

from  sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from models.enums import TaskStatus

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id",ondelete= "CASCADE"),nullable= False)
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullablle =True)
    status: Mapped[TaskStatus] = mapped_column(nullable= False, default =TaskStatus.TODO)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True)
    created_at: Mapped[datetime] =mapped_column(DateTime,nullable =False, server_dafault = func.now())


    def __repr__(self) -> str:
        return f"<Task(id={self.id},title={self.title}, status={self.status.value})>"
