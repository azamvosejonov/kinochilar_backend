import asyncio
from app.db.session import AsyncSessionLocal, engine
from app.models.movie import Genre
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select
from app.db import base # Ensures all models are registered

async def init_db():
    async with engine.begin() as conn:
        # Re-create all tables
        await conn.run_sync(base.Base.metadata.create_all)
    print("Database jadvallari yaratildi!")

async def seed_genres():
    genres = [
        {"uz": "Jangari", "ru": "Боевик"},
        {"uz": "Sarguzasht", "ru": "Приключения"},
        {"uz": "Komediya", "ru": "Комедия"},
        {"uz": "Drama", "ru": "Драма"},
        {"uz": "Qo'rqinchli", "ru": "Ужасы"},
        {"uz": "Fantastika", "ru": "Фантастика"},
        {"uz": "Triller", "ru": "Триллер"},
        {"uz": "Melodrama", "ru": "Мелодрама"},
        {"uz": "Multfilm", "ru": "Мультфильм"}
    ]
    async with AsyncSessionLocal() as db:
        for g in genres:
            stmt = select(Genre).where(Genre.name_uz == g["uz"])
            res = await db.execute(stmt)
            if res.scalars().first():
                continue
            genre = Genre(name_uz=g["uz"], name_ru=g["ru"])
            db.add(genre)
        await db.commit()
    print("Janrlar muvaffaqiyatli qo'shildi!")

async def create_admin():
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.email == "vosejonova@gmail.com")
        result = await db.execute(stmt)
        if result.scalars().first():
            print("Admin allaqachon mavjud.")
            return

        admin = User(
            email="vosejonova@gmail.com",
            hashed_password=get_password_hash("azam_770"),
            full_name="Admin Azam",
            is_superuser=True,
            is_active=True
        )
        db.add(admin)
        await db.commit()
    print("Admin muvaffaqiyatli yaratildi! (vosejonova@gmail.com / azam_770)")

async def main():
    await init_db()
    await seed_genres()
    await create_admin()

if __name__ == "__main__":
    asyncio.run(main())
