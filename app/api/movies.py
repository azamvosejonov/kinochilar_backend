from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models.movie import Movie, Genre, Episode, movie_genre
from app.schemas.movie import Movie as MovieSchema, MovieCreate, MovieUpdate, Genre as GenreSchema, Episode as EpisodeSchema, EpisodeCreate

router = APIRouter()

@router.get("/genres", response_model=List[GenreSchema])
async def get_genres(
    db: AsyncSession = Depends(get_db)
):
    """Get all genres for filtering"""
    stmt = select(Genre).order_by(Genre.name_uz)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/", response_model=List[MovieSchema])
async def list_movies(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    genre_id: Optional[int] = None,
    year: Optional[int] = None,
    min_rating: Optional[float] = None,
    query: Optional[str] = None,
    lang: str = "uz" # 'uz' or 'ru'
):
    stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags))
    
    if genre_id:
        stmt = stmt.join(Movie.genres).where(Genre.id == genre_id)
    
    if year:
        stmt = stmt.where(func.extract('year', Movie.created_at) == year)
    
    if min_rating:
        stmt = stmt.where(Movie.rating >= min_rating)
        
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
    Smart Search: Handles exact code match first, then fuzzy text search.
    """
    # 1. Exact match by code (Telegram style)
    code_stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).where(Movie.code == query)
    code_result = await db.execute(code_stmt)
    movie_by_code = code_result.scalars().first()
    if movie_by_code:
        return [movie_by_code]

    # 2. Text search on title and description (SQLite-compatible)
    title_field = Movie.title_ru if lang == "ru" else Movie.title_uz
    desc_field = Movie.description_ru if lang == "ru" else Movie.description_uz

    stmt = (
        select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags))
        .where(
            or_(
                title_field.ilike(f"%{query}%"),
                desc_field.ilike(f"%{query}%"),
                Movie.original_title.ilike(f"%{query}%"),
            )
        )
        .order_by(Movie.rating.desc())
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
    stmt = select(Movie).options(selectinload(Movie.genres), selectinload(Movie.tags)).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Increment views
    movie.views += 1
    await db.commit()

    return movie

@router.delete("/{movie_id}")
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_user)
):
    """Delete a movie (requires admin privileges)."""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    await db.delete(movie)
    await db.commit()
    
    return {"success": True, "message": "Movie deleted successfully"}

@router.put("/{movie_id}", response_model=MovieSchema)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_user)
):
    """Update a movie (requires admin privileges)."""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Update fields
    update_data = movie_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)
    
    await db.commit()
    await db.refresh(movie)
    
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

# Episode endpoints
@router.get("/{movie_id}/episodes", response_model=List[EpisodeSchema])
async def get_episodes(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all episodes for a movie/series"""
    stmt = select(Episode).where(Episode.movie_id == movie_id).order_by(Episode.season_number, Episode.episode_number)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{movie_id}/episodes", response_model=EpisodeSchema)
async def create_episode(
    movie_id: int,
    episode_in: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """Create a new episode for a series"""
    # Check if movie exists
    movie_stmt = select(Movie).where(Movie.id == movie_id)
    movie_result = await db.execute(movie_stmt)
    movie = movie_result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.is_series:
        raise HTTPException(status_code=400, detail="This is not a series")
    
    episode = Episode(**episode_in.model_dump(exclude={"movie_id"}), movie_id=movie_id)
    db.add(episode)
    await db.commit()
    await db.refresh(episode)
    return episode

@router.put("/episodes/{episode_id}", response_model=EpisodeSchema)
async def update_episode(
    episode_id: int,
    episode_in: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """Update an episode"""
    stmt = select(Episode).where(Episode.id == episode_id)
    result = await db.execute(stmt)
    episode = result.scalars().first()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    for field, value in episode_in.model_dump(exclude={"movie_id"}).items():
        setattr(episode, field, value)
    
    await db.commit()
    await db.refresh(episode)
    return episode

@router.delete("/episodes/{episode_id}")
async def delete_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """Delete an episode"""
    stmt = select(Episode).where(Episode.id == episode_id)
    result = await db.execute(stmt)
    episode = result.scalars().first()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    await db.delete(episode)
    await db.commit()
    return {"message": "Episode deleted successfully"}
