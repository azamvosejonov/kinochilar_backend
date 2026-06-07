from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime

class GenreBase(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None

class GenreCreate(GenreBase):
    pass

class Genre(GenreBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TagBase(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class EpisodeBase(BaseModel):
    season_number: int = 1
    episode_number: int
    title_uz: Optional[str] = None
    title_ru: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    video_url: str
    duration: Optional[int] = None

class EpisodeCreate(EpisodeBase):
    movie_id: int

class Episode(EpisodeBase):
    id: int
    movie_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MovieBase(BaseModel):
    code: Optional[str] = None
    title_uz: Optional[str] = None
    title_ru: Optional[str] = None
    original_title: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    release_date: Optional[date] = None
    duration: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    trailer_url: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str = "mp4"
    is_premium: int = 0
    is_series: bool = False

class MovieCreate(MovieBase):
    genre_ids: List[int] = []
    tag_ids: List[int] = []

class MovieUpdate(MovieBase):
    genre_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

class Movie(MovieBase):
    id: int
    rating: float
    vote_count: int
    views: int
    created_at: datetime
    genres: List[Genre] = []
    tags: List[Tag] = []
    episodes: List[Episode] = []

    model_config = ConfigDict(from_attributes=True)
