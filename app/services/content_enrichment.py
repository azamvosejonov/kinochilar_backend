import httpx
import logging
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.movie import Movie, Genre
from app.core.config import settings
from app.services import llm_service
import re

logger = logging.getLogger(__name__)

class ContentEnrichmentService:
    """
    Kino ma'lumotlarini AI va boshqa manbalar orqali boyitish.
    Tavsiflar, taglar, metadata qo'shish.
    """
    
    def __init__(self):
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.tmdb_api_key = settings.TMDB_API_KEY
    
    async def enrich_movie_description(self, movie: Movie, lang: str = 'uz') -> str:
        """
        AI orqali kino tavsifini boyitish.
        """
        try:
            title = movie.title_uz or movie.original_title
            current_desc = movie.description_uz or ""
            
            # Agar tavsif bo'sh bo'lsa yoki juda qisqa bo'lsa
            if len(current_desc) < 100:
                enriched_desc = await llm_service.generate_movie_description(title, lang=lang)
                if enriched_desc:
                    return enriched_desc
            
            # Mavjud tavsifni boyitish
            if current_desc:
                prompt = f"Quyidagi kino tavsifini yanada qiziqarli va professional qilib qayta yozib ber: '{current_desc}'"
                enriched_desc = await llm_service.generate_movie_description(title, lang=lang)
                if enriched_desc:
                    return enriched_desc
            
            return current_desc
            
        except Exception as e:
            logger.error(f"Tavsif boyitish xatosi: {e}")
            return movie.description_uz or ""
    
    async def generate_smart_tags(self, movie: Movie) -> List[str]:
        """
        AI orqali kino uchun smart taglar generatsiya qilish.
        """
        try:
            title = movie.title_uz or movie.original_title
            description = movie.description_uz or ""
            
            prompt = f"'{title}' kinosi uchun 10 ta mos tag (kalit so'z) generatsiya qil. Tavsif: '{description}'. Taglarni vergul bilan ajrating."
            
            enriched_desc = await llm_service.generate_movie_description(title, lang='uz')
            
            # Simple tag extraction from description
            tags = []
            common_words = ['kino', 'film', 'movie', 'serial', 'drama', 'komediya', 'action', 'fantastika']
            
            if description:
                words = re.findall(r'\b\w+\b', description.lower())
                tags = [word for word in words if len(word) > 3 and word not in common_words][:10]
            
            return tags
            
        except Exception as e:
            logger.error(f"Tag generatsiya xatosi: {e}")
            return []
    
    async def get_tmdb_enrichment(self, movie: Movie) -> Optional[Dict[str, Any]]:
        """
        TMDB'dan qo'shimcha ma'lumotlar olish.
        """
        try:
            if not self.tmdb_api_key:
                return None
            
            # Search by title
            search_url = f"{self.tmdb_base_url}/search/movie"
            params = {
                'api_key': self.tmdb_api_key,
                'query': movie.original_title or movie.title_uz,
                'language': 'uz-UZ'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results:
                        first_result = results[0]
                        
                        # Detailed movie info
                        movie_url = f"{self.tmdb_base_url}/movie/{first_result['id']}"
                        detail_params = {
                            'api_key': self.tmdb_api_key,
                            'language': 'uz-UZ',
                            'append_to_response': 'credits,videos,images'
                        }
                        
                        detail_response = await client.get(movie_url, params=detail_params)
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            return {
                                'tmdb_id': detail_data.get('id'),
                                'imdb_id': detail_data.get('imdb_id'),
                                'runtime': detail_data.get('runtime'),
                                'genres': [g['name'] for g in detail_data.get('genres', [])],
                                'production_companies': [c['name'] for c in detail_data.get('production_companies', [])],
                                'release_date': detail_data.get('release_date'),
                                'vote_average': detail_data.get('vote_average'),
                                'vote_count': detail_data.get('vote_count'),
                                'popularity': detail_data.get('popularity'),
                                'poster_path': f"https://image.tmdb.org/t/p/w500{detail_data.get('poster_path')}" if detail_data.get('poster_path') else None,
                                'backdrop_path': f"https://image.tmdb.org/t/p/original{detail_data.get('backdrop_path')}" if detail_data.get('backdrop_path') else None,
                                'trailer': self._extract_trailer(detail_data.get('videos', {}))
                            }
            
        except Exception as e:
            logger.error(f"TMDB enrichment xatosi: {e}")
            return None
    
    def _extract_trailer(self, videos_data: Dict) -> Optional[str]:
        """
        Videos data'dan trailer URL ini extract qilish.
        """
        try:
            results = videos_data.get('results', [])
            for video in results:
                if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                    return f"https://www.youtube.com/watch?v={video.get('key')}"
        except:
            pass
        return None
    
    async def enrich_movie(self, db: AsyncSession, movie_id: int) -> Dict[str, Any]:
        """
        Bitta kinoni to'liq boyitish.
        """
        try:
            stmt = select(Movie).where(Movie.id == movie_id)
            result = await db.execute(stmt)
            movie = result.scalars().first()
            
            if not movie:
                return {'success': False, 'error': 'Movie not found'}
            
            changes = []
            
            # 1. Tavsifni boyitish
            enriched_desc_uz = await self.enrich_movie_description(movie, 'uz')
            if enriched_desc_uz and enriched_desc_uz != movie.description_uz:
                movie.description_uz = enriched_desc_uz
                changes.append('description_uz')
            
            enriched_desc_ru = await self.enrich_movie_description(movie, 'ru')
            if enriched_desc_ru and enriched_desc_ru != movie.description_ru:
                movie.description_ru = enriched_desc_ru
                changes.append('description_ru')
            
            # 2. TMDB ma'lumotlari
            tmdb_data = await self.get_tmdb_enrichment(movie)
            if tmdb_data:
                if tmdb_data.get('poster_path') and not movie.poster_path:
                    movie.poster_path = tmdb_data['poster_path']
                    changes.append('poster_path')
                
                if tmdb_data.get('backdrop_path') and not movie.backdrop_path:
                    movie.backdrop_path = tmdb_data['backdrop_path']
                    changes.append('backdrop_path')
                
                if tmdb_data.get('trailer') and not movie.trailer_url:
                    movie.trailer_url = tmdb_data['trailer']
                    changes.append('trailer_url')
                
                if tmdb_data.get('runtime') and not movie.duration:
                    movie.duration = tmdb_data['runtime']
                    changes.append('duration')
                
                if tmdb_data.get('vote_average'):
                    movie.rating = tmdb_data['vote_average']
                    changes.append('rating')
            
            # 3. Smart tags
            tags = await self.generate_smart_tags(movie)
            if tags:
                # Taglarni databasega qo'shish (agar tag modeli bo'lsa)
                changes.append('tags')
            
            if changes:
                await db.commit()
                await db.refresh(movie)
                
                return {
                    'success': True,
                    'movie_id': movie.id,
                    'changes': changes,
                    'tmdb_data': tmdb_data
                }
            else:
                return {
                    'success': True,
                    'movie_id': movie.id,
                    'changes': [],
                    'message': 'No changes needed'
                }
                
        except Exception as e:
            logger.error(f"Movie enrichment xatosi: {e}")
            await db.rollback()
            return {'success': False, 'error': str(e)}
    
    async def batch_enrich_movies(self, db: AsyncSession, limit: int = 10) -> Dict[str, Any]:
        """
        Ko'p kinolarni boyitish.
        """
        try:
            # Enrichment kerak bo'lgan kinolarni topish
            stmt = select(Movie).where(
                (Movie.description_uz == None) | 
                (Movie.description_uz == '') |
                (Movie.poster_path == None) |
                (Movie.backdrop_path == None)
            ).limit(limit)
            
            result = await db.execute(stmt)
            movies = result.scalars().all()
            
            if not movies:
                return {'success': True, 'processed': 0, 'message': 'No movies need enrichment'}
            
            results = []
            for movie in movies:
                result = await self.enrich_movie(db, movie.id)
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
            logger.error(f"Batch enrichment xatosi: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
content_enrichment_service = ContentEnrichmentService()