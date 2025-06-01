from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api import article_api, hot_topic_api,final_pass_news#, analysis_api  # 필요한 api 모듈들
from app.scheduler import start_scheduler  # 스케줄러가 있다면

from app.db.findData import find_all_article

import logging
logger = logging.getLogger(__name__)
logger.info("✨ 로깅 시스템 작동 시작")

@asynccontextmanager
async def lifespan(app: FastAPI):
    import threading
    print("🚀 Lifespan: 스케줄러 백그라운드에서 실행 중...")
    threading.Thread(target=start_scheduler, daemon=True).start()
    yield
    print("🛑 Lifespan: 서버 종료!")


app = FastAPI(lifespan=lifespan)

# 절대 경로로 정적 파일 폴더 지정
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "front")

# 정적 파일 mount
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API 라우터 등록
app.include_router(article_api.router)
app.include_router(hot_topic_api.router)
app.include_router(final_pass_news.router)

# 기본 페이지
@app.get("/")
def root():
    return {"message": "🔥 News API Server is running!"}




# @app.get("/")
# def read_root():
#     return {"message": "Hot Topics Auto Pipeline Running!"}
