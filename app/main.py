from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings

# Import base to register ALL models before creating tables
from app.db import base  # noqa
from app.db.base_class import Base
from app.db.session import engine

from app.api import auth, movies, stream, discovery, users, comments, admin, user_content

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create upload directories
    from pathlib import Path
    upload_dir = Path("/home/azam/Desktop/yaratish/kinochilar/uploads")
    upload_dir.mkdir(exist_ok=True)
    (upload_dir / "videos").mkdir(exist_ok=True)
    (upload_dir / "posters").mkdir(exist_ok=True)
    (upload_dir / "backdrops").mkdir(exist_ok=True)
    
    yield
    # Shutdown: (nothing needed)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Kinochilar API ga xush kelibsiz!",
        "docs": "/docs",
        "version": settings.VERSION
    }

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(movies.router, prefix=f"{settings.API_V1_STR}/movies", tags=["movies"])
app.include_router(stream.router, prefix=f"{settings.API_V1_STR}/stream", tags=["stream"])
app.include_router(discovery.router, prefix=f"{settings.API_V1_STR}/discovery", tags=["discovery"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(comments.router, prefix=f"{settings.API_V1_STR}/comments", tags=["comments"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(user_content.router, prefix=f"{settings.API_V1_STR}/user", tags=["user-content"])

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="/home/azam/Desktop/yaratish/kinochilar/uploads"), name="uploads")
