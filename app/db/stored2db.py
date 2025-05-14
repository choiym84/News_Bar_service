# app/db/store_to_db.py

from collections import defaultdict
from datetime import datetime, timezone
from app.db.models import HotTopic, Article, ArticleSummary, AnalysisSummary, Publisher, Bridge
from app.db.database import SessionLocal


def merge_summaries(summary_lists):
    merged = []
    for s in summary_lists:
        merged.extend(s)
    return merged


def store_hot_topics_and_return_list(keywords: list):
    """
    [핫토픽 저장 함수]
    - 기존 activate=1 → 모두 0으로 비활성화
    - 새 키워드 → activate=1 상태로 저장
    - 결과: [{'name': '연금개혁', 'id': 1}, ...] 형태로 반환
    """
    db = SessionLocal()
    result = []

    try:
        # 1. 기존 핫토픽 비활성화
        db.query(HotTopic).filter(HotTopic.activate == 1).update({HotTopic.activate: 0})
        db.flush()

        # 2. 새 키워드 저장 (activate = 1)
        for keyword in keywords:
            topic = HotTopic(
                name=keyword,
                create_date=datetime.now(timezone.utc),
                activate=1
            )
            db.add(topic)
            db.flush()  # topic.id 확보

            result.append({
                "keyword": keyword,
                "id": topic.id
            })

        db.commit()
        print(f"[핫토픽 저장 완료] 총 {len(result)}개 저장됨.")
        return result

    except Exception as e:
        db.rollback()
        print("❌ 핫토픽 저장 실패:", e)
        return []

    finally:
        db.close()



def store_filtered_articles_and_return_info(filtered_articles: list, hot_topic_id: int) -> list:
    """
    필터링된 기사들을 DB에 저장하고 브릿지 테이블도 연결한 후, 정보 추출.

    Args:
        filtered_articles (list): 크롤링된 기사 리스트
        hot_topic_id (int): 해당 키워드 ID

    Returns:
        list[dict]: 저장된 기사들의 id, content, publisher, stance
    """
    db = SessionLocal()
    result = []

    try:
        for article in filtered_articles:
            
            publisher = db.query(Publisher).filter_by(name=article["publisher"]).first()
            if not publisher:
                continue

            # article["summary"] = {"노동자주장": ["휴일근무 반대","연봉인상"],"기업주장": ["근무시간 연장","성과위주 연봉협상"]}

            # 1. 기사 저장
            db_article = Article(
                publisher_id=publisher.id,
                title=article.get("title"),
                content=article.get("content"),
                url=article.get("link"),
                reporter=article.get("reporter"),
                publish_date=datetime.strptime(article["pub_date"], "%a, %d %b %Y %H:%M:%S %z")
            )
            db.add(db_article)
            db.flush()  # ID 확보

            # 2. 브릿지 테이블에 연결 저장
            bridge_entry = Bridge(
                hot_topics_id=hot_topic_id,
                articles_id=db_article.id
            )
            db.add(bridge_entry)

            # 3. 결과 저장용
            result.append({
                "id": db_article.id,
                "content": db_article.content,
                "publisher": article["publisher"],
                "stance": article["stance"]
            })

            summary_data = article.get("summary")  # 외부에서 같이 들어온 요약

            if summary_data:
                print("1")
                article_summary = ArticleSummary(
                    articles_id=db_article.id,
                    summary_text=summary_data,
                    hot_topics_id=hot_topic_id
                )
                db.add(article_summary)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ 기사 저장 중 에러: {e}")
    finally:
        db.close()

    return result
