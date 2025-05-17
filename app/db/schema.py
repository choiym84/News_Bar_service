from pydantic import BaseModel
from typing import Optional, List,Dict,Any
from datetime import datetime


# 📰 Article 스키마
class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    url: str
    reporter: Optional[str] = None
    publish_date: Optional[datetime] = None
    publisher: Optional[str] = None
    img_addr: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleRead(ArticleBase):
    id: int

    class Config:
        orm_mode = True


# 🏢 Publisher 스키마
class PublisherBase(BaseModel):
    name: str
    stance: Optional[str] = None


class PublisherRead(PublisherBase):
    id: int

    class Config:
        orm_mode = True


# 🔥 HotTopic 스키마
class HotTopicBase(BaseModel):
    name: str
    create_date: Optional[datetime] = None
    activate: bool


class HotTopicRead(HotTopicBase):
    id: int

    class Config:
        orm_mode = True


# 🔗 Bridge 스키마
class BridgeBase(BaseModel):
    hot_topics_id: int
    articles_id: int
    stance: Optional[str] = None


class BridgeRead(BridgeBase):
    id: int

    class Config:
        orm_mode = True


# 📝 ArticleSummary 스키마
class ArticleSummaryBase(BaseModel):
    summary_text: str  # JSON 필드
    create_date: Optional[datetime] = None
    hot_topics_id: int
    articles_id: int


class ArticleSummaryRead(ArticleSummaryBase):
    id: int

    class Config:
        orm_mode = True


# 📊 AnalysisSummary 스키마
class AnalysisSummaryBase(BaseModel):
    content: dict
    hot_topics_id: int


class AnalysisSummaryRead(AnalysisSummaryBase):
    id: int

    class Config:
        orm_mode = True


class GroupedArticleSummary(BaseModel):
    hot_topic_id: int
    stance: str
    content: List[ArticleSummaryBase]
