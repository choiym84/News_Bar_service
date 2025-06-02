# app/api/article_api.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.findData import check_summary_exists,find_all_article, find_article_by_id,get_headline_articles
from fastapi.responses import JSONResponse
from collections import defaultdict

router = APIRouter()
templates = Jinja2Templates(directory="app/front")

################################################################
# 기사 전체 목록 페이지 , 카테고리 별 X
# 웹버전
@router.get("/web/articles", response_class=HTMLResponse)
def get_articles(request: Request, page: int = 1, per_page: int = 10):
    articles = find_all_article(page,per_page)
    return templates.TemplateResponse("articles.html", {
        "request": request,
        "articles": articles["articles"],
        "current_page": articles["current_page"],
        "total_pages": articles["total_pages"],
        "total_articles": articles["total_articles"],
    })
# 앱 버전
@router.get("/app/articles")
def get_articles_json(page: int = 1, per_page: int = 10):
    try:



        articles = find_all_article(page, per_page)

        if not articles["articles"]:
            return JSONResponse(
                status_code=404,
                content={"status": "fail", "message": "기사를 찾을 수 없습니다."}
            )

        grouped_data = defaultdict(list)

        for a in articles["articles"]:
            category = a["category"]  # 예: '정치', '경제' 등
            grouped_data[category].append({
                "id": a["id"],
                "title": a["title"],
                "content": a["content"],
                # "description": a.get("summary", a["content"][:100] + "..."),  # 요약이 없으면 일부 본문
                "source": a["publisher"],
                "publishedAt": a["publish_date"]
                # "imageUrl": a["img_addr"],
                # "originalUrl": a["url"]
            })

        return JSONResponse(content={
            "status": "success",
            "data": grouped_data
        })
    
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500) 
################################################################

@router.get("/app/articles/{category}")
def get_articles_json(page: int = 1, per_page: int = 10,category:int = 100):
    try:

        articles = find_all_article(page, per_page,category=category)

        if not articles["articles"]:
            return JSONResponse(
                status_code=404,
                content={"status": "fail", "message": "기사를 찾을 수 없습니다."}
            )

        grouped_data = defaultdict(list)

        for a in articles["articles"]:
            category = a["category"]  # 예: '정치', '경제' 등
            grouped_data[category].append({
                "id": a["id"],
                "title": a["title"],
                "content": a["content"],
                # "description": a.get("summary", a["content"][:100] + "..."),  # 요약이 없으면 일부 본문
                "source": a["publisher"],
                "publishedAt": a["publish_date"],
                # "imageUrl": a["img_addr"],
                "originalUrl": a["url"]
            })

        return JSONResponse(content={
            "status": "success",
            "data": grouped_data
        })
    
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500) 


################################################################
# 기사 본문 페이지
@router.get("/web/article/{article_id}", response_class=HTMLResponse)
def get_article_detail(request: Request, article_id: int):
    article = find_article_by_id(article_id)
    return templates.TemplateResponse("article_view.html", {
        "request": request,
        "article": article
    })

# 기사 본문 페이지(앱)
@router.get("/app/article/{article_id}")
def get_article_detail(request: Request, article_id: int):

    try:
        article = find_article_by_id(article_id)
        if not article:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "해당 기사를 찾을 수 없습니다."}
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "created_at": article.publish_date.isoformat(),
                    "author": article.reporter
                    # 필요한 필드를 자유롭게 추가하세요
                }
            })
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)

################################################################
# 기사 요약 요청 페이지
@router.get("/web/article/{article_id}/summary")
def get_article_summary(request: Request,article_id:int):
    summary = check_summary_exists(article_id)
    if summary == None:
        return "good"

    return summary.summary_text

################################################################
#메인 화면의 헤드라인 기사들
@router.get("/web/main", response_class=HTMLResponse)
def get_main(request: Request):
    articles = get_headline_articles(limit=8)

    if not articles:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "헤드라인 기사가 없습니다."
        })

        # ✅ 정치 / 일반으로 분리
    political_articles = []
    general_articles = []

    political_articles = [a for a in articles if a["field"] == "정치"]
    general_articles = [a for a in articles if a["field"] != "정치"]

    return templates.TemplateResponse("headline.html", {
        "request": request,
        "political_articles": political_articles,
        "articles": general_articles
    })

#메인 화면의 헤드라인 기사들 (앱)
@router.get("/app/main")
def get_main_articles_for_app():

    try:
        articles = get_headline_articles(limit=8)

        if not articles:
            return JSONResponse(status_code=404, content={
                "status": "fail",
                "message": "헤드라인 기사가 없습니다."
            })

        # 정치 / 일반으로 분리
        political_articles = [a for a in articles if a["field"] == "정치"]
        general_articles = [a for a in articles if a["field"] != "정치"]

        return JSONResponse(content={
            "status": "success",
            "data": {
                "정치": [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "content": a["content"],
                        "publisher": a["publisher"],
                        "publishedAt": a["publish_date"].isoformat(),
                        "imageUrl": a["image"],
                        "originalUrl": a["url"]  # 필요 시 a["url"] 추가
                    }
                    for a in political_articles
                ],
                "일반": [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "content": a["content"],
                        "publisher": a["publisher"],
                        "publishedAt": a["publish_date"].isoformat(),
                        "imageUrl": a["image"],
                        "originalUrl": a["url"]
                    }
                    for a in general_articles
                ]
            }
        }
    )

    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)
    



    

