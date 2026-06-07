import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.movie import Movie, Genre
from app.core.config import settings
import random
import logging

logger = logging.getLogger(__name__)

async def fetch_and_populate_movies(db: AsyncSession, count: int, language: str = "uz-UZ"):
    """
    Uses TMDB API to find the best movies and adds them to our database.
    Supports Uzbek (uz-UZ) and Russian (ru-RU) localization.
    """
    tmdb_url = "https://api.themoviedb.org/3/movie/popular"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": language,
        "page": 1
    }
    
    added_count = 0
    page = 1
    
    # Increase timeout for potential network issues in Docker
    timeout = httpx.Timeout(20.0, connect=30.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        while added_count < count and page <= 10:
            params["page"] = page
            try:
                response = await client.get(tmdb_url, params=params)
                if response.status_code != 200:
                    logger.error(f"TMDB API error: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                logger.error(f"Connection to TMDB failed: {e}")
                break
                
            data = response.json()
            movies_data = data.get("results", [])
            
            for m in movies_data:
                if added_count >= count:
                    break
                
                # Check by original title or code to avoid duplicates
                stmt = select(Movie).where(Movie.original_title == m.get("original_title"))
                result = await db.execute(stmt)
                existing_movie = result.scalars().first()
                
                if existing_movie:
                    # Update translation for current language if movie exists
                    if "uz" in language:
                        existing_movie.title_uz = m["title"]
                        existing_movie.description_uz = m.get("overview")
                    else:
                        existing_movie.title_ru = m["title"]
                        existing_movie.description_ru = m.get("overview")
                    continue
                
                # New movie
                new_movie = Movie(
                    original_title=m.get("original_title"),
                    rating=m.get("vote_average", 0.0),
                    vote_count=m.get("vote_count", 0),
                    poster_path=f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}",
                    backdrop_path=f"https://image.tmdb.org/t/p/original{m.get('backdrop_path')}",
                    code=f"flm{random.randint(1000, 9999)}",
                    is_premium=0,
                    video_type="mp4" # Placeholder
                )
                
                # Metadata check for "1080p" awareness (e.g. in description)
                if "uz" in language:
                    new_movie.title_uz = m["title"]
                    new_movie.description_uz = (m.get("overview") or "") + "\n\nSifat: 1080p Full HD"
                else:
                    new_movie.title_ru = m["title"]
                    new_movie.description_ru = (m.get("overview") or "") + "\n\nКачество: 1080p Full HD"
                
                rd = m.get("release_date")
                if rd:
                    try:
                        from datetime import datetime
                        new_movie.release_date = datetime.strptime(rd, "%Y-%m-%d").date()
                    except:
                        pass

                db.add(new_movie)
                added_count += 1
            
            page += 1
            await db.commit()
            
    return added_count
