import httpx
import logging
import json
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.movie import Movie, Genre
from app.core.config import settings
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class LegalContentService:
    """
    Legal ochiq content manbalaridan kino ma'lumotlarini olish.
    Internet Archive, Public Domain, Creative Commons manbalaridan foydalanadi.
    """
    
    def __init__(self):
        self.legal_sources = {
            'internet_archive': {
                'base_url': 'https://archive.org/advancedsearch.php',
                'media_url': 'https://archive.org/details/',
                'name': 'Internet Archive'
            },
            'public_domain_movies': {
                'base_url': 'https://publicdomainmovies.net/api',
                'name': 'Public Domain Movies'
            },
            'wikimedia_commons': {
                'base_url': 'https://commons.wikimedia.org/w/api.php',
                'name': 'Wikimedia Commons'
            }
        }
    
    async def search_internet_archive(self, query: str, media_type: str = 'movies') -> List[Dict[str, Any]]:
        """
        Internet Archive'dan public domain filmlarni qidirish.
        """
        try:
            params = {
                'q': f'({query}) AND mediatype:({media_type})',
                'fl[]': ['identifier', 'title', 'year', 'description', 'creator', 'downloads'],
                'sort': 'downloads desc',
                'rows': 20,
                'output': 'json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.legal_sources['internet_archive']['base_url'],
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    docs = data.get('response', {}).get('docs', [])
                    
                    results = []
                    for doc in docs:
                        # Metadata olish
                        identifier = doc.get('identifier', '')
                        metadata = await self.get_archive_metadata(identifier)
                        
                        if metadata:
                            results.append({
                                'source': 'internet_archive',
                                'title': doc.get('title', ''),
                                'year': doc.get('year', ''),
                                'description': doc.get('description', ''),
                                'creator': doc.get('creator', ''),
                                'downloads': doc.get('downloads', 0),
                                'identifier': identifier,
                                'metadata': metadata
                            })
                    
                    logger.info(f"Internet Archive'dan {len(results)} ta topildi")
                    return results
                    
        except Exception as e:
            logger.error(f"Internet Archive qidirish xatosi: {e}")
            return []
    
    async def get_archive_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Internet Archive item metadata olish.
        """
        try:
            metadata_url = f"https://archive.org/metadata/{identifier}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(metadata_url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Video fayllarini topish
                    video_files = []
                    for file in data.get('files', []):
                        if file.get('format') in ['MPEG4', 'mp4', 'h.264']:
                            video_files.append({
                                'name': file.get('name'),
                                'url': f"https://archive.org/download/{identifier}/{file.get('name')}",
                                'size': file.get('size', 0),
                                'duration': file.get('duration', 0)
                            })
                    
                    # Rasm fayllarini topish
                    image_files = []
                    for file in data.get('files', []):
                        if file.get('format') in ['JPEG', 'PNG', 'GIF', 'Image']:
                            if 'poster' in file.get('name', '').lower() or 'cover' in file.get('name', '').lower():
                                image_files.append({
                                    'name': file.get('name'),
                                    'url': f"https://archive.org/download/{identifier}/{file.get('name')}",
                                    'type': 'poster' if 'poster' in file.get('name', '').lower() else 'cover'
                                })
                    
                    return {
                        'video_files': video_files,
                        'image_files': image_files,
                        'duration': data.get('metadata', {}).get('duration'),
                        'year': data.get('metadata', {}).get('year'),
                        'genre': data.get('metadata', {}).get('genre', []),
                        'rating': data.get('metadata', {}).get('rating', 0.0)
                    }
                    
        except Exception as e:
            logger.error(f"Metadata olish xatosi: {e}")
            return None
    
    async def search_public_domain_movies(self, query: str) -> List[Dict[str, Any]]:
        """
        Public domain movies manbalaridan qidirish.
        """
        try:
            # Bu yerda real API bo'lishi kerak, hozircha mock data
            # Haqiqiy loyihada API integration qilinadi
            
            mock_results = [
                {
                    'source': 'public_domain',
                    'title': f'Public Domain: {query}',
                    'year': '1950',
                    'description': 'Classic public domain movie',
                    'video_url': 'https://example.com/video.mp4',
                    'poster_url': 'https://example.com/poster.jpg'
                }
            ]
            
            return mock_results
            
        except Exception as e:
            logger.error(f"Public Domain qidirish xatosi: {e}")
            return []
    
    async def search_wikimedia_commons(self, query: str) -> List[Dict[str, Any]]:
        """
        Wikimedia Commons'dan media fayllarini qidirish.
        """
        try:
            params = {
                'action': 'query',
                'generator': 'search',
                'gsrsearch': f'{query} filetype:video',
                'gsrnamespace': '6',
                'gsrlimit': 20,
                'prop': 'imageinfo',
                'iiprop': 'url|extmetadata',
                'format': 'json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.legal_sources['wikimedia_commons']['base_url'],
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = data.get('query', {}).get('pages', {})
                    
                    results = []
                    for page_id, page_data in pages.items():
                        imageinfo = page_data.get('imageinfo', [])
                        if imageinfo:
                            results.append({
                                'source': 'wikimedia',
                                'title': page_data.get('title', ''),
                                'url': imageinfo[0].get('url', ''),
                                'description': page_data.get('description', ''),
                                'metadata': imageinfo[0].get('extmetadata', {})
                            })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Wikimedia qidirish xatosi: {e}")
            return []
    
    async def search_all_legal_sources(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Barcha legal manbalardan parallel qidirish.
        """
        tasks = [
            self.search_internet_archive(query),
            self.search_public_domain_movies(query),
            self.search_wikimedia_commons(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'internet_archive': results[0] if not isinstance(results[0], Exception) else [],
            'public_domain': results[1] if not isinstance(results[1], Exception) else [],
            'wikimedia': results[2] if not isinstance(results[2], Exception) else []
        }
    
    async def download_legal_content(self, content_data: Dict[str, Any], db: AsyncSession) -> Optional[Movie]:
        """
        Legal contentni yuklab databasega qo'shish.
        """
        try:
            # Dublikatni tekshirish
            stmt = select(Movie).where(Movie.original_title == content_data.get('title'))
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                logger.info(f"Kino allaqachon mavjud: {content_data.get('title')}")
                return existing
            
            # Yangi kino yaratish
            movie = Movie(
                original_title=content_data.get('title'),
                title_uz=content_data.get('title'),
                title_ru=content_data.get('title'),
                description_uz=content_data.get('description', ''),
                description_ru=content_data.get('description', ''),
                rating=content_data.get('metadata', {}).get('rating', 7.0),
                vote_count=content_data.get('downloads', 100),
                poster_path=content_data.get('poster_url'),
                backdrop_path=content_data.get('backdrop_url'),
                video_url=content_data.get('video_url'),
                video_type='mp4',
                is_premium=0,
                is_series=False,
                release_date=self._parse_year(content_data.get('year'))
            )
            
            db.add(movie)
            await db.commit()
            await db.refresh(movie)
            
            logger.info(f"Legal content qo'shildi: {movie.title_uz}")
            return movie
            
        except Exception as e:
            logger.error(f"Legal content yuklash xatosi: {e}")
            await db.rollback()
            return None
    
    def _parse_year(self, year_str: Optional[str]) -> Optional[str]:
        """
        Year stringni parse qilish.
        """
        if not year_str:
            return None
        
        try:
            # Year stringni tozalash
            year_match = re.search(r'\d{4}', str(year_str))
            if year_match:
                return year_match.group()
        except:
            pass
        
        return None
    
    async def populate_legal_movies(self, db: AsyncSession, queries: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        Legal filmlarni qidirib databasega qo'shish.
        """
        added_count = 0
        failed_count = 0
        results = []
        
        for query in queries:
            if added_count >= limit:
                break
            
            try:
                # Barcha manbalardan qidirish
                search_results = await self.search_all_legal_sources(query)
                
                # Internet Archive'dan eng yaxshi natijalarni olish
                archive_results = search_results.get('internet_archive', [])
                
                for content in archive_results:
                    if added_count >= limit:
                        break
                    
                    # Contentni databasega qo'shish
                    movie = await self.download_legal_content(content, db)
                    
                    if movie:
                        added_count += 1
                        results.append({
                            'title': movie.title_uz,
                            'source': 'legal',
                            'movie_id': movie.id
                        })
                    else:
                        failed_count += 1
                        
            except Exception as e:
                logger.error(f"Query '{query}' uchun xatolik: {e}")
                failed_count += 1
        
        return {
            'success': True,
            'added': added_count,
            'failed': failed_count,
            'results': results
        }

# Global instance
legal_content_service = LegalContentService()