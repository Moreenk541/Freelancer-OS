from datetime import datetime 
from typing import List, Optional

from sqlalchemy import Float, Text,DateTime,ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column,relationship

from app.database.database import Base

class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id",ondelete="CASCADE"),nullable=False)
    freelancer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete ="CASCADE"),nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable =True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable =True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(),nullable=False)

    def __repr__(self) ->str :
        return f"<TimeEntry(id={self.id}, duration={self.duration})>"
      
      


