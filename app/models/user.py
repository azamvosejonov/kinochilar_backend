from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean(), default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
