import asyncio
from app.db.session import AsyncSessionLocal
from app.models.movie import Movie
from app.models.user import User
from app.models.interactions import Review, Favorite
from app.db import base  # Ensures all models are registered
from sqlalchemy import select, delete

async def clear_movies():
    async with AsyncSessionLocal() as db:
        # Delete in correct order to avoid foreign key violations
        await db.execute(delete(Favorite))
        await db.execute(delete(Review))
        await db.execute(delete(Movie))
        await db.commit()
    print("Barcha kinolar o'chirildi!")

async def add_movies():
    from app.db.session import AsyncSessionLocal
    from app.models.movie import Movie
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        print("Dummy kinolar qo'shilmoqda...")
        
        # Add 3 dummy movies with video URLs
        movies = [
            Movie(
                title_uz="Avatar: Suv Yo'li",
                title_ru="Аватар: Путь воды",
                original_title="Avatar: The Way of Water",
                description_uz="Jek Salli va Neytiri yangi sarguzashtlarni boshdan kechiradilar.\n\nSifat: 1080p Full HD",
                description_ru="Джейк Салли и Нейтири отправляются в новое приключение.\n\nКачество: 1080p Full HD",
                code="avt001",
                rating=8.5,
                poster_path="https://image.tmdb.org/t/p/w500/t6Sna4vSjSBNmB0vYpZbn9pInS5.jpg",
                backdrop_path="https://image.tmdb.org/t/p/original/t6Sna4vSjSBNmB0vYpZbn9pInS5.jpg",
                video_url="https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
                video_type="mp4",
                duration=192
            ),
            Movie(
                title_uz="Qora Pantera",
                title_ru="Черная Пантера",
                original_title="Black Panther",
                description_uz="Vakanda qiroli o'z xalqini himoya qiladi.\n\nSifat: 1080p Full HD",
                description_ru="Король Ваканды защищает свой народ.\n\nКачество: 1080p Full HD",
                code="bp001",
                rating=9.0,
                poster_path="https://image.tmdb.org/t/p/w500/uxzzNc0Wle9x9P9uY2YurmqvG3P.jpg",
                backdrop_path="https://image.tmdb.org/t/p/original/uxzzNc0Wle9x9P9uY2YurmqvG3P.jpg",
                video_url="https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
                video_type="mp4",
                duration=134
            ),
            Movie(
                title_uz="O'rgimchak odam: Uyga yo'l yo'q",
                title_ru="Человек-паук: Нет пути домой",
                original_title="Spider-Man: No Way Home",
                description_uz="Piter Parker multivoqealar ichida qoladi.\n\nSifat: 1080p Full HD",
                description_ru="Питер Паркер оказывается в центре мультивселенной.\n\nКачество: 1080p Full HD",
                code="sm001",
                rating=8.8,
                poster_path="https://image.tmdb.org/t/p/w500/1g0dhvRrnspy6YDYFpC1S0EqpZp.jpg",
                backdrop_path="https://image.tmdb.org/t/p/original/1g0dhvRrnspy6YDYFpC1S0EqpZp.jpg",
                video_url="https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
                video_type="mp4",
                duration=148
            )
        ]
        
        db.add_all(movies)
        await db.commit()
        print("Bajarildi! 3 ta dummy kino qo'shildi.")

async def main():
    await clear_movies()
    await add_movies()

if __name__ == "__main__":
    asyncio.run(main())