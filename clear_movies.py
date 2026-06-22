import asyncio
from app.db.session import AsyncSessionLocal, engine
from app.models.movie import Movie
from sqlalchemy import select, delete

async def clear_movies():
    async with engine.begin() as conn:
        await conn.run_sync(Movie.__table__.delete())
    print("Barcha kinolar o'chirildi!")

async def main():
    await clear_movies()

if __name__ == "__main__":
    asyncio.run(main())