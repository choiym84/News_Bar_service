from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary
from sqlalchemy.orm import joinedload
from collections import defaultdict
from sqlalchemy import desc

#핫토픽 activate변경 함수
#기존 activate = 1 -> 0
#업데이트 하던 activate = 2 -> 1

def update_hot_topic_activate():
    db = SessionLocal()
    try:
        db.query(HotTopic).filter(HotTopic.activate == 1).update({HotTopic.activate: 0})
    
        db.flush()
        db.query(HotTopic).filter(HotTopic.activate == 2).update({HotTopic.activate: 1})
        db.commit()
    finally:
        db.close()

def update_headline_activate(data):
    db = SessionLocal()
    try:
        db.query(Article).filter(Article.id == data.id and Article.headline == 0).update({Article.headline:2})
        db.commit()
    finally:
        db.close()

def update_headline():
    db = SessionLocal()
    try:
        db.query(Article).filter(Article.headline == 1).update({Article.headline:0})
        db.flush()
        db.query(Article).filter(Article.headline == 2).update({Article.headline:1})
        db.commit()
    finally:
        db.close()