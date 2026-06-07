from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models.movie import Movie, Genre, movie_genre
from app.schemas.movie import Movie as MovieSchema, MovieCreate, MovieUpdate, Genre as GenreSchema

router = APIRouter()

@router.get("/", response_model=List[MovieSchema])
async def list_movies(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    genre_id: Optional[int] = None,
    query: Optional[str] = None,
    lang: str = "uz" # 'uz' or 'ru'
):
    stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags))
    
    if genre_id:
        stmt = stmt.join(Movie.genres).where(Genre.id == genre_id)
        
    if query:
        # Search in both languages or based on lang param
        if lang == "ru":
            stmt = stmt.where(
                or_(
                    Movie.title_ru.ilike(f"%{query}%"),
                    Movie.description_ru.ilike(f"%{query}%")
                )
            )
        else:
            stmt = stmt.where(
                or_(
                    Movie.title_uz.ilike(f"%{query}%"),
                    Movie.description_uz.ilike(f"%{query}%")
                )
            )
    
    stmt = stmt.offset(skip).limit(limit).order_by(Movie.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/search", response_model=List[MovieSchema])
async def search_movies(
    query: str,
    lang: str = "uz",
    db: AsyncSession = Depends(get_db)
):
    """
    Smart Search: Handles typos, fuzzy matches, and exact matches first.
    Uses PostgreSQL Trigram Similarity on localized fields.
    """
    # 1. Exact match by code (Telegram style)
    code_stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).where(Movie.code == query)
    code_result = await db.execute(code_stmt)
    movie_by_code = code_result.scalars().first()
    if movie_by_code:
        return [movie_by_code]
    
    # 2. Fuzzy Search
    title_field = Movie.title_ru if lang == "ru" else Movie.title_uz
    
    stmt = (
        select(Movie)
        .options(selectinload(Movie.genres), selectinload(Movie.tags))
        .where(
            or_(
                title_field.ilike(f"%{query}%"),
                func.similarity(title_field, query) > 0.3
            )
        )
        .order_by(
            # Rank optimization
            text(f"{title_field.name} <-> {repr(query)} ASC")
        )
        .limit(20)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/code/{code}", response_model=MovieSchema)
async def get_movie_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Quick lookup by code for Telegram bots."""
    stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).where(Movie.code == code)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@router.get("/{movie_id}", response_model=MovieSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Movie).options(
        selectinload(Movie.genres), 
        selectinload(Movie.tags),
        selectinload(Movie.credits)
    ).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Increment views
    movie.views += 1
    await db.commit()
    
    return movie

@router.post("/", response_model=MovieSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_in: MovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    # Process movie creation with tag_ids exclude fix
    movie = Movie(**movie_in.model_dump(exclude={"genre_ids", "tag_ids"}))
    
    if movie_in.genre_ids:
        result = await db.execute(select(Genre).where(Genre.id.in_(movie_in.genre_ids)))
        movie.genres = result.scalars().all()
        
    # Tags check
    if movie_in.tag_ids:
        from app.models.movie import Tag
        result = await db.execute(select(Tag).where(Tag.id.in_(movie_in.tag_ids)))
        movie.tags = result.scalars().all()

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie
