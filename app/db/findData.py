from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge
from sqlalchemy.orm import joinedload
from collections import defaultdict

#기사의 요약이 존재하는지
def check_summary_exists(article_id: int) -> bool:
    with SessionLocal() as db:
        summary = db.query(ArticleSummary).filter_by(articles_id=article_id).first()
        return summary is not None

#url 기반으로 기사 검색
def find_article_id_by_url(url: str) -> int | None:
    """
    주어진 URL에 해당하는 기사가 DB에 존재하면 ID 반환,
    없으면 None 반환.
    """
    with SessionLocal() as db:
        article = db.query(Article).filter_by(url=url).first()
        return article.id if article else None
    
#id 기반으로 기사 검색
def find_article_by_id(id: int) -> dict:
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == id).first()
        return article
    finally:
        db.close()

#db에 저장된 기사 다 불러오기
def find_all_article()->dict:
    db = SessionLocal()
    try:
        articles = db.query(Article).all()
        return [
            {
                "id": article.id,
                "url": article.url,
                "title": article.title,
                "content": article.content,
                "publisher": article.publisher,
                "reporter":article.reporter,
                "publish_date": article.publish_date.isoformat(),
            }
            for article in articles
        ]
    finally:
        db.close()

#핫토픽 id 가져오기
def find_activate_hottopic()->list:
    db = SessionLocal()
    try:
        #핫토픽 아이디 추출출
        active_topics = db.query(HotTopic).filter(HotTopic.activate == True).all()
        topic_ids = [t.id for t in active_topics]


        return topic_ids


    finally:
        db.close()

#핫토픽 id로 기사들 찾아오기
def find_article_by_hottopicId(id):
    db = SessionLocal()
    try:
        articles = db.query(Bridge).filter(Bridge.hot_topics_id == id).all()
        for i in articles:
            print(i.hot_topics_id,i.articles_id)

        print(len(articles))
    finally:
        db.close()


def hot_topic_pipeline():

    db = SessionLocal()
    try:
    # 1. 활성화된 hot_topic들 조회
        active_topic_ids = [t.id for t in db.query(HotTopic).filter(HotTopic.activate == True).all()]

        # 2. bridge 테이블에서 hot_topic_id로 필터
        bridges = db.query(Bridge)\
            .options(joinedload(Bridge.article))\
            .filter(Bridge.hot_topics_id.in_(active_topic_ids)).all()

        # 3. articles_id 리스트 추출
        article_ids = [b.articles_id for b in bridges]

        # 4. 요약 조회 (article과도 조인해서 가져옴)
        summaries = db.query(ArticleSummary)\
            .options(joinedload(ArticleSummary.article))\
            .filter(ArticleSummary.articles_id.in_(article_ids)).all()

        # 5. (hot_topic_id, stance) 기준으로 그룹핑
        grouped = defaultdict(list)

        # 요약마다 해당 Bridge 정보를 기반으로 그룹핑
        bridge_lookup = {(b.articles_id, b.hot_topics_id): b.stance for b in bridges}

        for summary in summaries:
            key = (summary.articles_id, summary.hot_topics_id)
            stance = bridge_lookup.get(key)
            if stance is None:
                continue
            grouped[(summary.hot_topics_id, stance)].append({
                "publisher": summary.article.publisher,
                "summary": summary.summary_text
            })

        # 6. 최종 응답 포맷으로 정리
        result = []
        for (hot_topic_id, stance), content in grouped.items():
            result.append({
                "hot_topic_id": hot_topic_id,
                "stance": stance,
                "content": content
            })

        return result

    finally:
        db.close()


        