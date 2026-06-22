from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.movie import Movie, Genre
from app.models.interactions import Ad, VisitLog
from app.schemas.movie import Movie as MovieSchema, Genre as GenreSchema
from app.schemas.ad import Ad as AdSchema
from pydantic import BaseModel, ConfigDict

router = APIRouter()

class HomeResponse(BaseModel):
    trending: List[MovieSchema]
    top_rated: List[MovieSchema]
    ads: List[AdSchema]
    genres: List[GenreSchema]

    model_config = ConfigDict(from_attributes=True)

@router.get("/home", response_model=HomeResponse)
async def get_home_discovery(db: AsyncSession = Depends(get_db)):
    """
    Returns data for the home page: Trending, Top Rated, Categories, and ADS.
    """
    # 1. Trending
    trending_stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).order_by(Movie.views.desc()).limit(10)
    trending = (await db.execute(trending_stmt)).scalars().all()

    # 2. Top Rated
    top_rated_stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).order_by(Movie.rating.desc()).limit(10)
    top_rated = (await db.execute(top_rated_stmt)).scalars().all()
    
    # 3. Ads
    ads_stmt = select(Ad).where(Ad.is_active == True).limit(5)
    ads = (await db.execute(ads_stmt)).scalars().all()
    
    # 4. Categories
    genres = (await db.execute(select(Genre).limit(20))).scalars().all()
    
    # Explicitly validate to convert SA models to Pydantic
    return HomeResponse.model_validate({
        "trending": trending,
        "top_rated": top_rated,
        "ads": ads,
        "genres": genres
    })

@router.post("/chat")
async def ai_consultant(query: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Movie).options(selectinload(Movie.genres)).limit(20)
    result = await db.execute(stmt)
    movies = result.scalars().all()
    movie_data = [{"id": m.id, "title": m.title_uz, "genres": [g.name_uz for g in m.genres]} for m in movies]
    from app.services import llm_service
    answer = await llm_service.ai_cinema_assistant(query, movie_data)
    return {"answer": answer}
