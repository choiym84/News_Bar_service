from app.utils.AI_Model.AI_main import ai_model3
from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary


def find_good_hottopic():
    db = SessionLocal()

    #핫토픽 아이디 추출출
    active_topics = db.query(HotTopic).all()
    topic_ids = [{'id':t.id,
                'keyword':t.name    
                    }
                    for t in active_topics]



    for hot in topic_ids:
        try:
            articles = db.query(Bridge).filter(Bridge.hot_topics_id == hot['id']).all()
        
        finally:
            db.close()
        message = f"{hot}의 기사의 개수 : {len(articles)}"
        print(message)

        with open("my_log.txt", "a", encoding="utf-8") as f:
            f.write(message + "\n")
        
            
            

        




