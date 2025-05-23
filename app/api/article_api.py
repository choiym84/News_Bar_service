# app/api/article_api.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.findData import check_summary_exists,find_all_article, find_article_by_id

router = APIRouter()
templates = Jinja2Templates(directory="app/front")

# 기사 목록 페이지
@router.get("/articles", response_class=HTMLResponse)
def get_articles(request: Request, page: int = 1, per_page: int = 10):
    articles = find_all_article(page,per_page)
    return templates.TemplateResponse("articles.html", {
        "request": request,
        "articles": articles["articles"],
        "current_page": articles["current_page"],
        "total_pages": articles["total_pages"],
        "total_articles": articles["total_articles"],
    })

# 기사 본문 페이지
@router.get("/article/{article_id}", response_class=HTMLResponse)
def get_article_detail(request: Request, article_id: int):
    article = find_article_by_id(article_id)
    return templates.TemplateResponse("article_view.html", {
        "request": request,
        "article": article
    })

@router.get("/article/{article_id}/summary")
def get_article_summary(request: Request,article_id:int):
    summary = check_summary_exists(article_id)
    if summary == None:
        return "good"

    return summary.summary_text