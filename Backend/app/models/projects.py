from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from models.enums import ProjectStatus

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key = True)
    freelancer_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"),nullable=False)
    title: Mapped[str] = mapped_column(String(255),nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable = True)
    status: Mapped[ProjectStatus] = mapped_column(nullable=False, default = ProjectStatus.DRAFT)
    deadline: Mapped[datetime] = mapped_column(DateTime,nullable= True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(),nullable=False)

    # Relationships
    freelancer: Mapped["User"] = relationship("User", back_populates="projects")
    client: Mapped["Client"] = relationship("Client", back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="project", cascade="all, delete-orphan"
    )
    files: Mapped[List["File"]] = relationship(
        "File", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title={self.title}, status={self.status.value})>"

      