import asyncio
from app.db.session import AsyncSessionLocal
from app.models.movie import Movie, Genre
from app.db import base # Ensures all models are registered
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("Dummy kinolar qo'shilmoqda...")
        
        # Check if any movies exist
        res = await db.execute(select(Movie).limit(1))
        if res.scalars().first():
            print("Kinolar allaqachon mavjud.")
            return

        # Add 3 dummy movies
        movies = [
            Movie(
                title_uz="Avatar: Suv Yo'li",
                title_ru="Аватар: Путь воды",
                original_title="Avatar: The Way of Water",
                description_uz="Jek Salli va Neytiri yangi sarguzashtlarni boshdan kechiradilar.\n\nSifat: 1080p Full HD",
                description_ru="Джейк Салли и Нейтири отправляются в новое приключение.\n\nКачество: 1080p Full HD",
                code="avt001",
                rating=8.5,
                poster_path="https://image.tmdb.org/t/p/w500/t6Sna4vSjSBNmB0vYpZbn9pInS5.jpg"
            ),
            Movie(
                title_uz="Qora Pantera",
                title_ru="Черная Пантера",
                original_title="Black Panther",
                description_uz="Vakanda qiroli o'z xalqini himoya qiladi.\n\nSifat: 1080p Full HD",
                description_ru="Король Ваканды защищает свой народ.\n\nКачество: 1080p Full HD",
                code="bp001",
                rating=9.0,
                poster_path="https://image.tmdb.org/t/p/w500/uxzzNc0Wle9x9P9uY2YurmqvG3P.jpg"
            ),
            Movie(
                title_uz="O'rgimchak odam: Uyga yo'l yo'q",
                title_ru="Человек-паук: Нет пути домой",
                original_title="Spider-Man: No Way Home",
                description_uz="Piter Parker multivoqealar ichida qoladi.\n\nSifat: 1080p Full HD",
                description_ru="Питер Паркер оказывается в центре мультивселенной.\n\nКачество: 1080p Full HD",
                code="sm001",
                rating=8.8,
                poster_path="https://image.tmdb.org/t/p/w500/1g0dhvRrnspy6YDYFpC1S0EqpZp.jpg"
            )
        ]
        
        db.add_all(movies)
        await db.commit()
        print("Bajarildi! 3 ta dummy kino qo'shildi.")

if __name__ == "__main__":
    asyncio.run(main())
