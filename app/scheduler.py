from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime
from app.services.hot_topics.pipeline import start_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler():
    logger.info("✅ 스케줄러 시작: 3시간마다 파이프라인 실행")
    scheduler.add_job(
        start_pipeline,
        trigger=IntervalTrigger(hours=3),# ✅ 테스트할 땐 seconds=10 으로! hours=3
        # next_run_time=datetime.now(),
        id="hot_topic_pipeline",
        replace_existing=True
    )
    scheduler.start()

    
