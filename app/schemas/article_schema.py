from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    description: str
    source: str
    publishedAt: datetime
    imageUrl: Optional[str]
    originalUrl: str

class ArticleRequest(BaseModel):
    url: str