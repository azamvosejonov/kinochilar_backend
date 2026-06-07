from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api import deps
from app.db.session import get_db
from app.models.interactions import Review
from app.models.movie import Movie
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

class CommentCreate(BaseModel):
    content: Optional[str] = None
    rating: float # 1-10

class Comment(BaseModel):
    id: int
    content: Optional[str]
    rating: float
    user_id: int
    movie_id: int
    user_name: str

    class Config:
        from_attributes = True

@router.get("/movie/{movie_id}", response_model=List[Comment])
async def list_movie_comments(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Review).where(Review.movie_id == movie_id).options(selectinload(Review.user))
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    
    return [
        Comment(
            id=r.id, 
            content=r.content, 
            rating=r.rating, 
            user_id=r.user_id, 
            movie_id=r.movie_id,
            user_name=r.user.full_name or r.user.email
        ) for r in reviews
    ]

@router.post("/movie/{movie_id}", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment_or_rating(
    movie_id: int,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # AI Moderation
    from app.services import llm_service
    is_ok = await llm_service.moderate_comment(comment_in.content or "")
    if not is_ok:
        raise HTTPException(status_code=400, detail="Izoh odob-axloq qoidalariga to'g'ri kelmadi.")

    comment = Review(

        content=comment_in.content,
        rating=comment_in.rating,
        user_id=current_user.id,
        movie_id=movie_id
    )
    db.add(comment)
    
    # Simple logic to update average rating
    # New Rating = (Current Rating * Vote Count + New Rating) / (Vote Count + 1)
    movie.rating = ((movie.rating * movie.vote_count) + comment_in.rating) / (movie.vote_count + 1)
    movie.vote_count += 1
    
    await db.commit()
    await db.refresh(comment)
    
    return Comment(
        id=comment.id,
        content=comment.content,
        rating=comment.rating,
        user_id=comment.user_id,
        movie_id=comment.movie_id,
        user_name=current_user.full_name or current_user.email
    )
