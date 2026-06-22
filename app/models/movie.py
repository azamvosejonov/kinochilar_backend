from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Float, Date, Table, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import date, datetime

# Many-to-many link tables
movie_genre = Table(
    "movie_genre",
    Base.metadata,
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("genre_id", ForeignKey("genre.id"), primary_key=True),
)

movie_credits = Table(
    "movie_credits",
    Base.metadata,
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("person_id", ForeignKey("person.id"), primary_key=True),
    Column("role", String(50)),
    Column("character", String(255)),
)

movie_tag = Table(
    "movie_tag",
    Base.metadata,
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)

class Tag(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name_uz: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    name_ru: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    tag_movies: Mapped[List["Movie"]] = relationship("Movie", secondary=movie_tag, back_populates="tags")

class Person(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name_uz: Mapped[str] = mapped_column(String(255), index=True)
    name_ru: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    biography_uz: Mapped[Optional[str]] = mapped_column(Text)
    biography_ru: Mapped[Optional[str]] = mapped_column(Text)
    profile_path: Mapped[Optional[str]] = mapped_column(String(255))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    
    person_movies: Mapped[List["Movie"]] = relationship("Movie", secondary=movie_credits, back_populates="credits")

class Genre(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name_uz: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    name_ru: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    genre_movies: Mapped[List["Movie"]] = relationship("Movie", secondary=movie_genre, back_populates="genres")

class Movie(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True) 
    title_uz: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    title_ru: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    original_title: Mapped[Optional[str]] = mapped_column(String(255))
    description_uz: Mapped[Optional[str]] = mapped_column(Text)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)
    
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    
    poster_path: Mapped[Optional[str]] = mapped_column(String(255))
    backdrop_path: Mapped[Optional[str]] = mapped_column(String(255))
    trailer_url: Mapped[Optional[str]] = mapped_column(String(255))
    video_url: Mapped[Optional[str]] = mapped_column(String(255))
    video_type: Mapped[str] = mapped_column(String(20), default="mp4")
    
    is_premium: Mapped[int] = mapped_column(Integer, default=0)
    is_series: Mapped[bool] = mapped_column(Boolean, default=False) # True if this is a series
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False) # True if admin approved
    views: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    genres: Mapped[List["Genre"]] = relationship("Genre", secondary=movie_genre, back_populates="genre_movies")
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=movie_tag, back_populates="tag_movies")
    credits: Mapped[List["Person"]] = relationship("Person", secondary=movie_credits, back_populates="person_movies")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    episodes: Mapped[List["Episode"]] = relationship("Episode", back_populates="movie", cascade="all, delete-orphan")

class Episode(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"), nullable=False)
    
    season_number: Mapped[int] = mapped_column(Integer, default=1)
    episode_number: Mapped[int] = mapped_column(Integer)
    title_uz: Mapped[Optional[str]] = mapped_column(String(255))
    title_ru: Mapped[Optional[str]] = mapped_column(String(255))
    description_uz: Mapped[Optional[str]] = mapped_column(Text)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)
    
    video_url: Mapped[str] = mapped_column(String(255)) # Link to this specific episode
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    movie: Mapped["Movie"] = relationship("Movie", back_populates="episodes")
