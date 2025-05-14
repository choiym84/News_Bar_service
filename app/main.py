from fastapi import FastAPI
from app.scheduler import start_scheduler
from contextlib import asynccontextmanager
from app.api import hot_topic_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Lifespan: 스케줄러 시작 중...")
    start_scheduler()
    yield  # 여기까지 실행되면 서버가 준비됨
    print("🛑 Lifespan: 서버 종료!")

app = FastAPI(lifespan=lifespan)

app.include_router(hot_topic_api.router)


@app.get("/")
def read_root():
    return {"message": "Hot Topics Auto Pipeline Running!"}
