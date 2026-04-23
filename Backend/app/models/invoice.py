from datetime import datetime
from typing import List, Optional

from sqlalchemy import Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from models.enums import InvoiceStatus

class Invoice(Base):
    __tablename__ ="invoices"

    id: Mapped[int] = mapped_column(primary_key =True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id",ondelete ="CASCADE"),nullable= False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete = "CASCADE"), nullable= False)
    freelancer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable= False)
    hours_worked:Mapped[float] =mapped_column(Float, nullable=False)
    hourly_rate: Mapped[float] =mapped_column(Float,nullable=False)
    total_amount: Mapped[float] =mapped_column(Float,nullable= False)
    status: Mapped[InvoiceStatus] =mapped_column(nullable=False,default = InvoiceStatus.DRAFT)
    due_date:Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime]= mapped_column(DateTime, server_default=func.now(),nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="invoices")
    client: Mapped["Client"] = relationship("Client", back_populates="invoices")
    freelancer: Mapped["User"] = relationship("User", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, total={self.total_amount}, status={self.status.value})>"