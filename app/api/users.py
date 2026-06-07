from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models.interactions import Favorite, Watchlist, UserCollection
from app.models.movie import Movie
from app.schemas.movie import Movie as MovieSchema
from app.models.user import User

router = APIRouter()

@router.post("/favorites/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Check if movie exists
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    fav = Favorite(user_id=current_user.id, movie_id=movie_id)
    db.add(fav)
    try:
        await db.commit()
    except:
        await db.rollback()
        return {"message": "Already in favorites"}
    return {"message": "Added to favorites"}

@router.delete("/favorites/{movie_id}")
async def remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    stmt = delete(Favorite).where(Favorite.user_id == current_user.id, Favorite.movie_id == movie_id)
    await db.execute(stmt)
    await db.commit()
    return {"message": "Removed from favorites"}

@router.get("/favorites", response_model=List[MovieSchema])
async def get_my_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    stmt = select(Movie).join(Favorite).where(Favorite.user_id == current_user.id).options(selectinload(Movie.genres))
    result = await db.execute(stmt)
    return result.scalars().all()
