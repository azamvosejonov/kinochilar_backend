import httpx
import logging
import os
import re
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.movie import Movie
from app.core.config import settings
import yt_dlp
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoDownloadService:
    """AI-powered video download service that finds and downloads movie videos."""
    
    def __init__(self):
        # Vercel da /tmp/, lokalda project/data/movies/
        if os.getenv("VERCEL"):
            self.download_dir = Path("/tmp/kinochilar/movies")
        else:
            self.download_dir = Path(__file__).parent.parent.parent / "data" / "movies"
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    async def search_video_sources(self, movie_title: str, movie_year: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        AI-powered search for video sources using multiple platforms.
        Returns list of potential video sources with metadata.
        """
        sources = []
        
        # Search query construction
        search_query = f"{movie_title} trailer"
        if movie_year:
            search_query += f" {movie_year}"
        
        try:
            # YouTube search using yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                
                if search_results and 'entries' in search_results:
                    for entry in search_results['entries'][:5]:  # Top 5 results
                        sources.append({
                            'platform': 'YouTube',
                            'title': entry.get('title', ''),
                            'url': entry.get('url', ''),
                            'duration': entry.get('duration', 0),
                            'thumbnail': entry.get('thumbnail', ''),
                            'quality': 'HD' if entry.get('duration', 0) > 0 else 'Unknown'
                        })
            
            logger.info(f"Found {len(sources)} video sources for '{movie_title}'")
            return sources
            
        except Exception as e:
            logger.error(f"Error searching video sources: {e}")
            return []
    
    async def download_video(self, video_url: str, movie_id: int, quality: str = 'best') -> Optional[str]:
        """
        Download video from URL and save to local storage.
        Returns the local file path if successful.
        """
        try:
            # Create movie-specific directory
            movie_dir = self.download_dir / str(movie_id)
            movie_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp for download
            ydl_opts = {
                'format': f'{quality}[ext=mp4]/best[ext=mp4]/best',
                'outtmpl': str(movie_dir / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['uz', 'ru'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                # Get the downloaded file path
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    # Rename to standard format
                    new_filename = movie_dir / f"video_{movie_id}.mp4"
                    os.rename(filename, new_filename)
                    logger.info(f"Successfully downloaded video for movie {movie_id}")
                    return str(new_filename.relative_to(self.download_dir))
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    async def process_movie_video(self, db: AsyncSession, movie_id: int) -> Dict[str, Any]:
        """
        Complete workflow: search, select best source, and download video for a movie.
        """
        try:
            # Get movie from database
            stmt = select(Movie).where(Movie.id == movie_id)
            result = await db.execute(stmt)
            movie = result.scalars().first()
            
            if not movie:
                return {'success': False, 'error': 'Movie not found'}
            
            # Skip if video already exists
            if movie.video_url:
                return {'success': False, 'error': 'Video already exists'}
            
            # Search for video sources
            sources = await self.search_video_sources(
                movie.title_uz or movie.original_title,
                movie.release_date.year if movie.release_date else None
            )
            
            if not sources:
                return {'success': False, 'error': 'No video sources found'}
            
            # Select best source (prefer longer duration, HD quality)
            best_source = max(sources, key=lambda x: (x['duration'], x['quality'] == 'HD'))
            
            # Download video
            video_path = await self.download_video(best_source['url'], movie_id)
            
            if video_path:
                # Update movie with video path
                movie.video_url = video_path
                await db.commit()
                
                return {
                    'success': True,
                    'video_path': video_path,
                    'source': best_source,
                    'movie_id': movie_id
                }
            else:
                return {'success': False, 'error': 'Download failed'}
                
        except Exception as e:
            logger.error(f"Error processing movie video: {e}")
            await db.rollback()
            return {'success': False, 'error': str(e)}
    
    async def batch_process_movies(self, db: AsyncSession, limit: int = 5) -> Dict[str, Any]:
        """
        Process multiple movies that don't have videos yet.
        """
        try:
            # Get movies without videos
            stmt = select(Movie).where(Movie.video_url == None).limit(limit)
            result = await db.execute(stmt)
            movies = result.scalars().all()
            
            if not movies:
                return {'success': True, 'processed': 0, 'message': 'No movies without videos'}
            
            results = []
            for movie in movies:
                result = await self.process_movie_video(db, movie.id)
                results.append({
                    'movie_id': movie.id,
                    'title': movie.title_uz,
                    'result': result
                })
            
            successful = sum(1 for r in results if r['result']['success'])
            
            return {
                'success': True,
                'processed': len(movies),
                'successful': successful,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
video_service = VideoDownloadService()