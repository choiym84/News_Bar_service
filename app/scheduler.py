# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.interval import IntervalTrigger
# import logging
# from datetime import datetime
# from app.services.hot_topics.pipeline import start_pipeline

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# scheduler = AsyncIOScheduler()

# def start_scheduler():
#     logger.info("✅ 스케줄러 시작: 3시간마다 파이프라인 실행")
#     scheduler.add_job(
#         start_pipeline,
#         trigger=IntervalTrigger(hours=3),# ✅ 테스트할 땐 seconds=10 으로! hours=3
#         next_run_time=datetime.now(),
#         id="hot_topic_pipeline",
#         replace_existing=True
#     )
#     scheduler.start()

    # ✅ app/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler  # 🔁 변경됨
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime
from app.services.hot_topics.pipeline import start_pipeline  # 동기 함수
from app.services.hot_topics.headline import headline_update

import threading  # 🔁 백그라운드 실행을 위한 추가

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    def job():
        logger.info("✅ 스케줄러 시작: 3시간마다 파이프라인 실행")
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            start_pipeline,
            trigger=IntervalTrigger(hours=3),  # 테스트용: seconds=10
            # next_run_time=datetime.now(),
            id="hot_topic_pipeline",
            replace_existing=True
        )

        scheduler.add_job(
            headline_update,
            trigger=IntervalTrigger(minutes=100),
            id="headline_update_job",
            # next_run_time=datetime.now(),
            replace_existing=True
        )
        scheduler.start()

    # 🔁 FastAPI의 이벤트 루프와 격리된 백그라운드 스레드에서 실행
    threading.Thread(target=job, daemon=True).start()

