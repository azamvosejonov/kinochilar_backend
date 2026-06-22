import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

# Use PostgreSQL URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def create_admin_user():
    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == "kaxorovorif6@gmail.com")
        result = await session.execute(stmt)
        existing_admin = result.scalars().first()
        
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            email="kaxorovorif6@gmail.com",
            full_name="Admin",
            hashed_password=get_password_hash("azam_770"),
            is_superuser=True,
            is_active=True
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"Admin user created successfully! ID: {admin_user.id}")
        print("Email: kaxorovorif6@gmail.com")
        print("Password: azam_770")

if __name__ == "__main__":
    asyncio.run(create_admin_user())