from app.utils.AI_Model.summary import summarize_with_chatgpt
from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary


def update_summary():
    db = SessionLocal()
    try:
        #핫토픽 아이디 추출출

        active_ids = db.query(HotTopic).filter(HotTopic.activate == 1).all()

        a = []
        for i in active_ids:
            print(i.id)
            bridges = db.query(Bridge).filter(Bridge.hot_topics_id == i.id).all()
            for b in bridges:
                article = db.query(Article).filter(Article.id == b.articles_id).first()
                a = summarize_with_chatgpt(article.content)
                summary = db.query(ArticleSummary).filter(
                    ArticleSummary.articles_id == article.id
                ).first()
                summary.summary_text = a
                
            
            
    

        db.commit()
    
    finally:
        db.close()








