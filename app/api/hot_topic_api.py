# app/api/hot_topic_api.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.findData import hot_topic_pipeline

router = APIRouter()
templates = Jinja2Templates(directory="app/front")

# 핫토픽 요약을 보여주는 웹 페이지
@router.get("/hottopics", response_class=HTMLResponse)
def get_hot_topics(request: Request):
    topics = hot_topic_pipeline()
    return templates.TemplateResponse("hot_topics.html", {
        "request": request,
        "topics": topics
    })
