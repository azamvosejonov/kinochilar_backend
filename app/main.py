import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings

# Import base to register ALL models before creating tables
from app.db import base  # noqa
from app.db.base_class import Base
from app.db.session import engine

from app.api import auth, movies, stream, discovery, users, comments, admin, user_content

# Upload directory — /tmp on Vercel, local path on dev
IS_VERCEL = bool(os.getenv("VERCEL"))
if IS_VERCEL:
    UPLOAD_DIR = Path("/tmp/kinochilar/uploads")
else:
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create upload directories
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "videos").mkdir(exist_ok=True)
    (UPLOAD_DIR / "posters").mkdir(exist_ok=True)
    (UPLOAD_DIR / "backdrops").mkdir(exist_ok=True)

    yield

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
try:
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
except RuntimeError:
    pass  # Already mounted or path doesn't exist yet
