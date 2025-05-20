from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api import article_api, hot_topic_api#, analysis_api  # 필요한 api 모듈들
from app.scheduler import start_scheduler  # 스케줄러가 있다면

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Lifespan: 스케줄러 시작 중...")
    start_scheduler()
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
# app.include_router(analysis_api.router)

# 기본 페이지
@app.get("/")
def root():
    return {"message": "🔥 News API Server is running!"}


from fastapi import FastAPI
# from app.scheduler import start_scheduler
# from contextlib import asynccontextmanager
# from app.api import hot_topic_api
# from fastapi.staticfiles import StaticFiles
# import os
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("🚀 Lifespan: 스케줄러 시작 중...")
#     start_scheduler()
#     yield  # 여기까지 실행되면 서버가 준비됨
#     print("🛑 Lifespan: 서버 종료!")

# app = FastAPI(lifespan=lifespan)
# # ✅ 절대 경로 설정
# current_dir = os.path.dirname(os.path.abspath(__file__))
# static_dir = os.path.join(current_dir, "front")

# app.mount("/static", StaticFiles(directory=static_dir), name="static")
# app.include_router(hot_topic_api.router)


# @app.get("/")
# def read_root():
#     return {"message": "Hot Topics Auto Pipeline Running!"}
