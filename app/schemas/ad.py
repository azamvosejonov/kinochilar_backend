from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class AdBase(BaseModel):
    title_uz: str
    title_ru: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None
    is_active: bool = True
    target_movie_id: Optional[int] = None

class AdCreate(AdBase):
    pass

class AdUpdate(AdBase):
    title_uz: Optional[str] = None
    image_url: Optional[str] = None

class Ad(AdBase):
    id: int
    views: int
    clicks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
