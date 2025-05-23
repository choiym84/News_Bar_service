from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary
from sqlalchemy.orm import joinedload
from collections import defaultdict
from sqlalchemy import desc

#기사의 요약이 존재하는지
def check_summary_exists(article_id: int) -> bool:
    with SessionLocal() as db:
        summary = db.query(ArticleSummary).filter_by(articles_id=article_id).first()
        return summary if summary else None

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
def find_all_article(page=1,per_page=10)->dict:
    db = SessionLocal()
    try:
        total_articles = db.query(Article).count()
        articles = db.query(Article).order_by(desc(Article.publish_date)).offset((page - 1) * per_page).limit(per_page).all()
        article_list = [
            {
                "id": article.id,
                "url": article.url,
                "title": article.title,
                "content": article.content,
                "publisher": article.publisher,
                "reporter":article.reporter,
                "publish_date": article.publish_date.strftime('%Y-%m-%d'),
            }
            for article in articles
        ]

        return {
            "articles": article_list,
            "current_page": page,
            "total_pages": (total_articles + per_page - 1) // per_page,
            "total_articles": total_articles,
        }
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
        # 1. 활성화된 핫토픽 조회
        active_topics = db.query(HotTopic).filter(HotTopic.activate == 1).all()
        hot_topics = [{"id": t.id, "name": t.name} for t in active_topics]

        result = []



        for topic in hot_topics:
            topic_id = topic["id"]
            topic_name = topic["name"]

            analysis = db.query(AnalysisSummary)\
                .filter(AnalysisSummary.hot_topics_id == topic['id'])\
                .order_by(AnalysisSummary.id.desc())\
                .first()

            # 2. 해당 핫토픽 ID의 브릿지 가져오기
            bridges = db.query(Bridge)\
                .options(joinedload(Bridge.article))\
                .filter(Bridge.hot_topics_id == topic_id).all()

            # 3. article_id → stance 매핑
            article_to_stance = {b.articles_id: b.stance for b in bridges}
            article_ids = list(article_to_stance.keys())

            # 4. 요약 가져오기
            summaries = db.query(ArticleSummary)\
                .options(joinedload(ArticleSummary.article))\
                .filter(ArticleSummary.articles_id.in_(article_ids)).all()

            # 5. 정치 성향별 그룹핑
            grouped_by_stance = {"진보": [], "중립": [], "보수": []}

            for summary in summaries:
                stance = article_to_stance.get(summary.articles_id)
                if stance not in grouped_by_stance:
                    continue

                grouped_by_stance[stance].append({
                    "publisher": summary.article.publisher,
                    "summary": summary.summary_text,
                    "article_id": summary.article.id
                })

            # 6. 결과에 추가
            result.append({
                "id": topic_id,
                "name": topic_name,
                "groups": grouped_by_stance,
                "analysis":analysis.content
            })

        return result

    finally:
        db.close()