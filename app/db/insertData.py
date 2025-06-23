from app.db.database import SessionLocal
from app.db.models import HotTopic, Article, ArticleSummary, AnalysisSummary, Publisher, Bridge
from datetime import datetime
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Dict
from app.utils.AWS_img import upload_image_to_s3_from_url
from urllib.parse import urlparse, parse_qs
#핫토픽 저장하는 함수
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
        # 1. 기존 핫토픽 비활성화 -> 나중에 하기로 정함. updataData.py로 가보기.
        

        # 2. 새 키워드 저장 (activate = 2)
        for keyword in keywords:
            topic = HotTopic(
                name=keyword,
                create_date=datetime.now(timezone.utc),
                activate=2
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


#기사 요약을 저장하는 함수
def summary_insert(summary_text,article_id,hot_topic_id):
    """
    - article: DB에 저장된 Article 객체 또는 dict (id, content 포함)
    - 요약이 없으면 생성 후 ArticleSummary로 저장
    """

    db = SessionLocal()
    try:
        
        existing = db.query(ArticleSummary).filter_by(articles_id=article_id).first()
        if existing:
            return  # 이미 요약이 존재하면 아무것도 하지 않음

        # 저장
        summary_entry = ArticleSummary(
            articles_id=article_id,
            summary_text=summary_text,
            hot_topics_id=hot_topic_id
        )
        db.add(summary_entry)
        db.commit()
        

    except Exception as e:
        db.rollback()
        print("❌ 요약 저장 실패:", e)
    finally:
        db.close()

#기사 리스트를 저장하는 함수
#아마 핫토픽용 저장 함수가 될 듯
def save_article(article_data: dict,is_headline=0) -> int | None:
    """
    기사 URL이 존재하지 않으면 새로 저장하고 ID와 keyword 반환
    """
    # 저장용 세션 분리
    db = SessionLocal()
    try:

        thumbnail = upload_image_to_s3_from_url(img_url=article_data['img_url'],s3_key=article_data['link'])
        
        parsed_url = urlparse(article_data['link'])
        sid = parse_qs(parsed_url.query).get('sid', [None])[0]

        # 🔄 sid → 카테고리 매핑
        sid_map = {
            '100': '정치',
            '101': '경제',
            '102': '사회',
            '103': '생활/문화',
            '104': '세계',
            '105': 'IT/과학',
            '154': '대선'
        }
        category = sid_map.get(sid, '기타')

        # 기사 발행 시간에 대한 부분분
        try:
            publish_date = datetime.strptime(article_data["pub_date"], "%a, %d %b %Y %H:%M:%S %z")
        except KeyError:
            publish_date = datetime.utcnow()


        new_article = Article(
            title=article_data["title"],
            content=article_data["content"],
            url=article_data["link"],
            reporter=article_data["reporter"],
            publish_date=publish_date,
            publisher=article_data["publisher"],
            img_addr=thumbnail,
            field=category,
            headline = is_headline
        )
        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        return new_article.id
    except Exception as e:
        db.rollback()
        print(f"Error saving article: {e}")
        return None
    finally:
        db.close()


def bridge_conn(article_id,hot_topics_id,stance):
    db = SessionLocal()

    try:
        bridge_entry = Bridge(hot_topics_id=hot_topics_id, articles_id=article_id,stance=stance)
        db.add(bridge_entry)
        db.commit()
        db.refresh(bridge_entry)
        return bridge_entry
    except Exception as e:
        db.rollback()
        print(f"Bridge 삽입 오류: {e}")
        return None
    finally:
        db.close()


def save_analyze(text, hot_topic_id):
    db = SessionLocal()
    try:
        # 1. hot_topic_id로 기존 데이터 조회
        existing = db.query(AnalysisSummary).filter(AnalysisSummary.hot_topics_id == hot_topic_id).first()

        if existing:
            # 2. 있으면 업데이트
            existing.content = text
        else:
            # 3. 없으면 새로 삽입
            existing = AnalysisSummary(hot_topics_id=hot_topic_id, content=text)
            db.add(existing)

        db.commit()
        db.refresh(existing)
        return existing

    except Exception as e:
        db.rollback()
        print(f"AnalysisSummary 삽입/수정 오류: {e}")
        return None

    finally:
        db.close()

