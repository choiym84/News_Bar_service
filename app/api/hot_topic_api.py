from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import HotTopic, Article, ArticleSummary, Publisher,Bridge
from app.db.schema import ArticleRead,ArticleSummaryRead
from typing import List
from app.db.findData import find_all_article,hot_topic_pipeline,find_article_by_hottopicId,find_article_by_id
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

templates = Jinja2Templates(directory="app/front")

router = APIRouter()
@router.get("/articles", response_model=List[ArticleRead])
def read_articles():
    return find_all_article()


@router.get("/hottopic",response_model=List[ArticleSummaryRead])
def hottopic():
    
    #id 가져옴.
    return hot_topic_pipeline()

@router.get("/article/{article_id}", response_class=HTMLResponse)
def get_article_content(request: Request,article_id: int):
    article = find_article_by_id(article_id)
    return templates.TemplateResponse("article_view.html", {
            "request": request,
            "article": article
        })
    
        


    