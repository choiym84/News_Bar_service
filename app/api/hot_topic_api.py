# app/api/hot_topic_api.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.findData import hot_topic_pipeline,find_activate_hottopic,find_hottopic_detail_by_id,find_analysis_by_hot_topic_id
from fastapi.responses import JSONResponse
router = APIRouter()
templates = Jinja2Templates(directory="app/front")

# 핫토픽 요약을 보여주는 웹 페이지
@router.get("/web/hottopics", response_class=HTMLResponse)
def get_hot_topics(request: Request):
    topics = hot_topic_pipeline()
    print(topics)

    # return topics
    return templates.TemplateResponse("hot_topics.html", {
        "request": request,
        "topics": topics
    })


#앱 전용 hottopic들만 던져준다. 그럼 그걸로 요약들을 찾아온다.

@router.get("/app/hottopics")
def get_hot_topics_json():
    try:
        topics = find_activate_hottopic()  # [{'id': 203, 'keyword': '국방부 민간인 장관'}, ...]

        keyword_items = [
            {"id": t["id"], "keyword": t["keyword"]}
            for t in topics
            if "id" in t and "keyword" in t
        ]

        return JSONResponse(content={
            "status": "success",
            "data": {
                "keywords": keyword_items
            }
        })
    
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)


#이제 키워드 클릭하면 키워드에 더 자세한 내용 응답.
@router.get("/app/hottopic/{hot_topic_id}")
def get_hot_topic_detail(hot_topic_id: int):
    # DB에서 해당 ID의 핫토픽 상세 정보 조회
    try:
        detail = find_hottopic_detail_by_id(hot_topic_id)

        if not detail:
            return JSONResponse(status_code=404, content={
                "status": "fail",
                "message": "해당 핫토픽 정보를 찾을 수 없습니다."
            })

        return JSONResponse(content={
            "status": "success",
            "data": detail
        })
    
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)


@router.get("/app/hottopic/{hot_topic_id}/analysis")
def get_hot_topic_detail(hot_topic_id: int):
    # DB에서 해당 ID의 핫토픽 상세 정보 조회
    try:
        detail = find_analysis_by_hot_topic_id(hot_topic_id)

        if not detail:
            return JSONResponse(status_code=404, content={
                "status": "fail",
                "message": "해당 핫토픽 비교분석 정보를 찾을 수 없습니다."
            })

        return JSONResponse(content={
            "status": "success",
            "data": detail
        })
    
    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)





