import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.db.session import get_db
from app.models.movie import Movie

router = APIRouter()

# Simple chunk generator for streaming
def send_bytes_range_requests(
    file_path: str, start: int, end: int, chunk_size: int = 10 * 1024
):
    with open(file_path, "rb") as f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            yield f.read(read_size)

@router.get("/{movie_id}")
async def stream_movie(
    movie_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_url:
        raise HTTPException(status_code=404, detail="Video not found for this movie")
    
    # Check if remote URL or local file
    if movie.video_url.startswith("http://") or movie.video_url.startswith("https://"):
        # For remote URLs, redirect to the video
        return RedirectResponse(url=movie.video_url)
    
    # For local files
    video_path = f"/data/movies/{movie.video_url}"
    
    if not os.path.exists(video_path):
         raise HTTPException(status_code=404, detail="File not found on server")

    file_size = os.stat(video_path).st_size
    range_header = request.headers.get("range")
    
    if range_header:
        # Handling range request
        range_str = range_header.replace("bytes=", "")
        start_str, end_str = range_str.split("-")
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
        
        chunk = send_bytes_range_requests(video_path, start, end)
        
        return StreamingResponse(
            chunk,
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
            },
            media_type="video/mp4",
        )
    
    # Full file request
    return StreamingResponse(
        open(video_path, "rb"),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )
