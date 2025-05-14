from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import HotTopic, Article, ArticleSummary, Publisher

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
def get_active_summaries(db: Session = Depends(get_db)):
    # 1. 활성화된 키워드만 가져오기
    hot_topics = db.query(HotTopic).filter(HotTopic.activate == 1).all()
    result = []

    for topic in hot_topics:
        # 2. 해당 키워드에 연결된 기사 ID 가져오기
        articles = db.query(Article).filter(Article.hot_topic_id == topic.id).all()
        summaries = []

        for article in articles:
            summary = db.query(ArticleSummary).filter_by(article_id=article.id).first()
            publisher = db.query(Publisher).filter_by(id=article.publisher_id).first()

            if summary and publisher:
                summaries.append({
                    "publisher": publisher.name,
                    "summary": summary.summary_json
                })

        result.append({
            "keyword": topic.name,
            "id": topic.id,
            "summaries": summaries
        })

    return result
