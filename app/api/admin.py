from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import os
import shutil
from pathlib import Path
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.movie import Movie, Genre, Tag, Episode
from app.models.user import User
from app.models.interactions import Review, Notification, Ad, VisitLog
from app.models.ai_growth import AILog, AIStat
from app.schemas.movie import (
    Movie as MovieSchema, MovieCreate, MovieUpdate, 
    Genre as GenreSchema, GenreCreate, TagCreate, EpisodeCreate, Episode as EpisodeSchema
)
from app.schemas.user import User as UserSchema
from app.schemas.ad import Ad as AdSchema, AdCreate, AdUpdate
from pydantic import BaseModel
from app.services import ai_service, management_ai, video_service, legal_content_service
from app.services.content_enrichment import ContentEnrichmentService

router = APIRouter()

# Initialize services
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

class NotificationCreate(BaseModel):
    title: str
    message: str
    user_id: Optional[int] = None

class SimpleMovieCreate(BaseModel):
    title_uz: str
    title_ru: Optional[str] = None
    original_title: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = "mp4"

# --- ADMIN STATISTICS & AI DASHBOARD ---

@router.get("/stats/overview")
async def get_stats_overview(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Admin Dashboard Stats + AI performance."""
    total_users = await db.scalar(select(func.count(User.id)))
    yesterday = datetime.now() - timedelta(days=1)
    new_users = await db.scalar(select(func.count(User.id)).where(User.created_at >= yesterday))
    
    # AI Performance Stats
    today_ai_stat = await db.scalar(select(AIStat).where(func.date(AIStat.date) == datetime.now().date()))
    ai_logs_stmt = select(AILog).order_by(AILog.created_at.desc()).limit(10)
    ai_logs = (await db.execute(ai_logs_stmt)).scalars().all()
    
    return {
        "users": {"total": total_users, "new_24h": new_users},
        "ai_performance": {
            "today_acquired": today_ai_stat.users_acquired if today_ai_stat else 0,
            "today_descriptions": today_ai_stat.descriptions_generated if today_ai_stat else 0,
            "recent_actions": [{"action": l.action_type, "desc": l.description, "time": l.created_at} for l in ai_logs]
        }
    }

@router.post("/ai/trigger-autonomous")
async def trigger_ai_autonomous(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Manually trigger AI to start managing and growing the site."""
    result = await management_ai.run_autonomous_growth(db)
    return result

# --- OTHER CRUD ENDPOINTS ---
@router.post("/genres", response_model=GenreSchema)
async def create_genre(genre_in: GenreCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(deps.get_current_active_superuser)):
    genre = Genre(**genre_in.model_dump())
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return genre

@router.post("/episodes", response_model=EpisodeSchema)
async def create_episode(ep_in: EpisodeCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(deps.get_current_active_superuser)):
    movie = await db.get(Movie, ep_in.movie_id)
    if not movie: raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.is_series: movie.is_series = True
    episode = Episode(**ep_in.model_dump())
    db.add(episode)
    await db.commit()
    await db.refresh(episode)
    return episode

@router.post("/movies", response_model=MovieSchema)
async def admin_create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(deps.get_current_active_superuser)):
    movie = Movie(**movie_in.model_dump(exclude={"genre_ids", "tag_ids"}))
    if movie_in.genre_ids:
        res = await db.execute(select(Genre).where(Genre.id.in_(movie_in.genre_ids)))
        movie.genres = res.scalars().all()
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    
    # Auto-enrich the movie with AI
    try:
        enrichment_result = await content_enrichment_service.enrich_movie(db, movie.id)
        if enrichment_result.get('success'):
            await db.refresh(movie)
    except Exception as e:
        # Don't fail if enrichment fails
        pass
    
    return movie

@router.post("/movies/simple", response_model=MovieSchema)
async def admin_create_simple_movie(
    movie_in: SimpleMovieCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Create a movie with minimal info - AI will auto-enrich it."""
    movie = Movie(
        title_uz=movie_in.title_uz,
        title_ru=movie_in.title_ru or movie_in.title_uz,
        original_title=movie_in.original_title or movie_in.title_uz,
        video_url=movie_in.video_url,
        video_type=movie_in.video_type,
        rating=7.0,  # Default rating
        views=0
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    
    # Auto-enrich the movie with AI
    try:
        enrichment_result = await content_enrichment_service.enrich_movie(db, movie.id)
        if enrichment_result.get('success'):
            await db.refresh(movie)
    except Exception as e:
        # Don't fail if enrichment fails
        pass
    
    return movie

@router.get("/users", response_model=List[UserSchema])
async def list_users(db: AsyncSession = Depends(get_db), current_admin = Depends(deps.get_current_active_superuser)):
    return (await db.execute(select(User))).scalars().all()

@router.post("/ads", response_model=AdSchema)
async def create_ad(ad_in: AdCreate, db: AsyncSession = Depends(get_db), current_admin = Depends(deps.get_current_active_superuser)):
    ad = Ad(**ad_in.model_dump()); db.add(ad); await db.commit(); await db.refresh(ad); return ad

# --- VIDEO DOWNLOAD ENDPOINTS ---

@router.post("/video/download/{movie_id}")
async def download_movie_video(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Manually trigger video download for a specific movie."""
    result = await video_service.process_movie_video(db, movie_id)
    return result

@router.post("/video/batch-download")
async def batch_download_videos(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Batch download videos for movies without videos."""
    result = await video_service.batch_process_movies(db, limit)
    return result

@router.get("/video/sources/{movie_id}")
async def get_video_sources(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Search for available video sources for a movie."""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    sources = await video_service.search_video_sources(
        movie.title_uz or movie.original_title,
        movie.release_date.year if movie.release_date else None
    )
    
    return {"movie_id": movie_id, "sources": sources}

# --- LEGAL CONTENT ENDPOINTS ---

@router.post("/legal/search")
async def search_legal_content(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Search for legal content from public domain sources."""
    results = await legal_content_service.search_all_legal_sources(query)
    return {"query": query, "results": results}

@router.post("/legal/populate")
async def populate_legal_movies(
    queries: list[str],
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Populate database with legal content from public domain sources."""
    result = await legal_content_service.populate_legal_movies(db, queries, limit)
    return result

# --- CONTENT ENRICHMENT ENDPOINTS ---

@router.post("/enrich/{movie_id}")
async def enrich_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Enrich a single movie with AI-generated content and metadata."""
    result = await content_enrichment_service.enrich_movie(db, movie_id)
    return result

@router.post("/enrich/batch")
async def batch_enrich_movies(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Batch enrich multiple movies with AI-generated content."""
    result = await content_enrichment_service.batch_enrich_movies(db, limit)
    return result

# --- FILE UPLOAD ENDPOINTS ---

@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Upload video file from computer."""
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
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Upload poster image file from computer."""
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
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Upload backdrop image file from computer."""
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

# --- USER CONTENT APPROVAL ENDPOINTS ---

@router.get("/user-content")
async def get_user_content(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
):
    """Get all user-submitted content waiting for approval"""
    stmt = select(Movie).where(Movie.is_approved == False).order_by(Movie.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/user-content/{movie_id}/approve")
async def approve_user_content(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_active_superuser)
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
    current_admin = Depends(deps.get_current_active_superuser)
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
