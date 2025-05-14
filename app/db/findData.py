from app.db.database import SessionLocal
from app.db.models import ArticleSummary
from app.db.models import Article

def check_summary_exists(article_id: int) -> bool:
    with SessionLocal() as db:
        summary = db.query(ArticleSummary).filter_by(articles_id=article_id).first()
        return summary is not None

def find_article_id_by_url(url: str) -> int | None:
    """
    주어진 URL에 해당하는 기사가 DB에 존재하면 ID 반환,
    없으면 None 반환.
    """
    with SessionLocal() as db:
        article = db.query(Article).filter_by(url=url).first()
        return article.id if article else None
    
def find_article_by_id(id: int) -> dict:
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == id).first()
        return article
    finally:
        db.close()