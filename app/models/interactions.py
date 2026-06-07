from typing import List, Optional
from sqlalchemy import Column, Integer, String, Table, Text, ForeignKey, Float, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime

# Many-to-many for collections
collection_movie = Table(
    "collection_movie",
    Base.metadata,
    Column("collection_id", ForeignKey("usercollection.id"), primary_key=True),
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
)

class Review(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship("User")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="reviews")

class Favorite(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='_user_movie_favorite_uc'),)

class UserCollection(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    user: Mapped["User"] = relationship("User")
    movies: Mapped[List["Movie"]] = relationship("Movie", secondary=collection_movie)

class Watchlist(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='_user_movie_watchlist_uc'),)

class History(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), nullable=False)
    watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    progress: Mapped[int] = mapped_column(Integer, default=0)

class Ad(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title_uz: Mapped[str] = mapped_column(String(255))
    title_ru: Mapped[Optional[str]] = mapped_column(String(255))
    image_url: Mapped[str] = mapped_column(String(255))
    link_url: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_movie_id: Mapped[Optional[int]] = mapped_column(ForeignKey("movie.id"), nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class VisitLog(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    page_url: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Notification(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean(), default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[Optional["User"]] = relationship("User")
