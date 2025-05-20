# app/api/article_api.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.findData import find_all_article, find_article_by_id

router = APIRouter()
templates = Jinja2Templates(directory="app/front")

# 기사 목록 페이지
@router.get("/articles", response_class=HTMLResponse)
def get_articles(request: Request):
    articles = find_all_article()
    return templates.TemplateResponse("articles.html", {
        "request": request,
        "articles": articles
    })

# 기사 본문 페이지
@router.get("/article/{article_id}", response_class=HTMLResponse)
def get_article_detail(request: Request, article_id: int):
    article = find_article_by_id(article_id)
    return templates.TemplateResponse("article_view.html", {
        "request": request,
        "article": article
    })