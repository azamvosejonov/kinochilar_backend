from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from pathlib import Path
import uuid
import shutil

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.movie import Movie
from app.services.content_enrichment import ContentEnrichmentService

router = APIRouter()
content_enrichment_service = ContentEnrichmentService()

# Upload directories — /tmp on Vercel, local path on dev
import os as _os
if _os.getenv("VERCEL"):
    UPLOAD_DIR = Path("/tmp/kinochilar/uploads")
else:
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = UPLOAD_DIR / "videos"
POSTER_DIR = UPLOAD_DIR / "posters"
BACKDROP_DIR = UPLOAD_DIR / "backdrops"
VIDEO_DIR.mkdir(exist_ok=True)
POSTER_DIR.mkdir(exist_ok=True)
BACKDROP_DIR.mkdir(exist_ok=True)

class UserMovieCreate(BaseModel):
    title_uz: str
    title_ru: Optional[str] = None
    original_title: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = "mp4"
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    is_series: Optional[bool] = False

@router.post("/movies/submit")
async def submit_user_movie(
    movie_in: UserMovieCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Foydalanuvchi o'z profili orqali yangi kino joylashtiradi.
    AI bilan takrorlanmasligini tekshiradi va ma'lumotlarni boyitadi.
    """
    
    # Takrorlanmasligini tekshirish (nomi bilan)
    stmt = select(Movie).where(
        (Movie.title_uz.ilike(f"%{movie_in.title_uz}%")) |
        (Movie.original_title.ilike(f"%{movie_in.original_title or movie_in.title_uz}%"))
    )
    result = await db.execute(stmt)
    existing_movies = result.scalars().all()
    
    if existing_movies:
        # Agar juda o'xshash kino bo'lsa, xato berish
        for existing in existing_movies:
            similarity = calculate_similarity(
                movie_in.title_uz.lower(),
                existing.title_uz.lower()
            )
            if similarity > 0.8:  # 80% o'xshashlik
                raise HTTPException(
                    status_code=400,
                    detail=f"Bu kino allaqachon mavjud: {existing.title_uz}"
                )
    
    # Yangi kino yaratish
    movie = Movie(
        title_uz=movie_in.title_uz,
        title_ru=movie_in.title_ru or movie_in.title_uz,
        original_title=movie_in.original_title or movie_in.title_uz,
        video_url=movie_in.video_url,
        video_type=movie_in.video_type,
        description_uz=movie_in.description_uz,
        description_ru=movie_in.description_ru,
        poster_path=movie_in.poster_path,
        backdrop_path=movie_in.backdrop_path,
        rating=7.0,  # Default rating
        views=0,
        is_premium=0,  # User submitted movies are not premium by default
        is_series=movie_in.is_series or False,
        is_approved=False  # User submitted movies need admin approval
    )
    
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    
    # AI bilan boyitish
    try:
        enrichment_result = await content_enrichment_service.enrich_movie(db, movie.id)
        if enrichment_result.get('success'):
            await db.refresh(movie)
    except Exception as e:
        # Don't fail if enrichment fails
        pass
    
    return {
        "success": True,
        "message": "Kino muvaffaqiyatli joylashtirildi! AI ma'lumotlarni to'ldirmoqda.",
        "movie_id": movie.id,
        "movie": movie
    }

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Simple string similarity calculation using Levenshtein distance.
    """
    if not str1 or not str2:
        return 0.0
    
    # Simple similarity based on common words
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Upload video file from computer for user content."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Only video files are allowed")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = VIDEO_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return file URL
    file_url = f"/uploads/videos/{unique_filename}"
    
    return {
        "success": True,
        "file_url": file_url,
        "filename": unique_filename,
        "original_filename": file.filename
    }

@router.post("/upload/poster")
async def upload_poster(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Upload poster image file from computer for user content."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = POSTER_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return file URL
    file_url = f"/uploads/posters/{unique_filename}"
    
    return {
        "success": True,
        "file_url": file_url,
        "filename": unique_filename,
        "original_filename": file.filename
    }

@router.post("/upload/backdrop")
async def upload_backdrop(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Upload backdrop image file from computer for user content."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = BACKDROP_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Return file URL
    file_url = f"/uploads/backdrops/{unique_filename}"
    
    return {
        "success": True,
        "file_url": file_url,
        "filename": unique_filename,
        "original_filename": file.filename
    }

# Admin endpoints for user content approval
@router.get("/user-content")
async def get_user_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Get all user-submitted content waiting for approval"""
    stmt = select(Movie).where(Movie.is_approved == False).order_by(Movie.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/user-content/{movie_id}/approve")
async def approve_user_content(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Approve user-submitted content"""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie.is_approved = True
    await db.commit()
    await db.refresh(movie)
    
    return {"success": True, "message": "Content approved successfully"}

@router.post("/user-content/{movie_id}/reject")
async def reject_user_content(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Reject and delete user-submitted content"""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    await db.delete(movie)
    await db.commit()
    
    return {"success": True, "message": "Content rejected and deleted"}