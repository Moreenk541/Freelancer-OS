from datetime import datetime

from sqlalchemy import String, DateTime,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column, relationship

from app.database.database  import Base

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"),nullable= False)
    uploaded_by:Mapped[int] =mapped_column(ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    file_name: Mapped[str] = mapped_column(String(255),nullable=False)
    file_url: Mapped[str] = mapped_column(String(700),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(),nullable=False)

    def __repr__(self) -> str:
        return f"<File(id={self.id}, file_name={self.file_name})>"