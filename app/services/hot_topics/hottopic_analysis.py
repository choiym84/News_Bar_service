from app.utils.AI_Model.AI_main import ai_model3
from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary


def update_analysis():
    db = SessionLocal()

    #핫토픽 아이디 추출
    active_topics = db.query(HotTopic).filter(HotTopic.activate == 1).all()
    topic_ids = [{'id':t.id,
                'keyword':t.name    
                    }
                    for t in active_topics]



    for hot in topic_ids:
        try:
            articles = db.query(Bridge).filter(Bridge.hot_topics_id == hot['id']).all()
        
        finally:
            db.close()

        ids = []
        for article in articles:
            ids.append({'article_id':article.articles_id,'stance':article.stance})

        ai_model3(ids,hot)




