import asyncio
from app.db.session import AsyncSessionLocal
from app.services.ai_service import fetch_and_populate_movies

async def main():
    async with AsyncSessionLocal() as db:
        print("Kinolarni yig'ish boshlandi...")
        count = await fetch_and_populate_movies(db, count=5, language="uz-UZ")
        print(f"Bajarildi! {count} ta kino qo'shildi.")

if __name__ == "__main__":
    asyncio.run(main())
