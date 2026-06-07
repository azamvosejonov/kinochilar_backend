from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str
    suggested_movie_ids: List[int] = []
