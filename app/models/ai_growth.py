from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime

class AILog(Base):
    """Logs of everything the AI does to manage and grow the site."""
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action_type: Mapped[str] = mapped_column(String(100)) # 'acquisition', 'description', 'maintenance'
    description: Mapped[str] = mapped_column(Text)
    impact_score: Mapped[int] = mapped_column(Integer, default=0) # Estimate of impact (e.g., users brought)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AIStat(Base):
    """Daily stats for AI performance."""
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    users_acquired: Mapped[int] = mapped_column(Integer, default=0)
    descriptions_generated: Mapped[int] = mapped_column(Integer, default=0)
    marketing_suggestions: Mapped[int] = mapped_column(Integer, default=0)
