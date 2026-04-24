from datetime import datetime


from sqlalchemy import String, DateTime,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column, relationship


from app.database.database  import Base

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Relationships
    users: Mapped["User"]= relationship("User", back_populates="roles")

    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"
    