from app.db.database import SessionLocal
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary
from sqlalchemy.orm import joinedload
from collections import defaultdict
from sqlalchemy import desc,text
from app.utils.AWS_img import download_from_AWS_s3


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
        
        try:
            img = None
            if article.img_addr != "https://our-capstone06.s3.amazonaws.com/article_img/NoExistThumbnail.jpg":
                img = download_from_AWS_s3(article.img_addr)
        except Exception as e:
            print(f"S3에서 이미지 다운로드 실패 {e}")

        return article,img
    finally:
        db.close()

#db에 저장된 기사 다 불러오기 + 카테고리 별로 나눌 수 있어야 함.
def find_all_article(page=1, per_page=10, category=100) -> dict:
    db = SessionLocal()
    try:

        query = db.query(Article)

        category_id = "전체"

        if category == 100:
            category_id = '정치'

        elif category == 101:
            category_id = '경제'

        elif category == 102:
            category_id = '사회'

        elif category == 103:
            category_id = '생활/문화'

        elif category == 104:
            category_id = '세계'

        elif category == 105:
            category_id = 'IT/과학'

        elif category == 154:
            category_id = '대선'


        # 🔍 카테고리가 "전체"가 아닌 경우만 필터 적용
        if category != "전체":
            query = query.filter(Article.field == category_id)

        # 개수 계산
        total_articles = query.count()

        # 정렬 + 페이징
        articles = query.order_by(desc(Article.publish_date)) \
                        .offset((page - 1) * per_page) \
                        .limit(per_page).all()

        print(query)
        headline = []
        # 데이터 변환
        article_list = []
        for article in articles:

            try:
                img = None
                if article.img_addr != "https://our-capstone06.s3.amazonaws.com/article_img/NoExistThumbnail.jpg":
                    img = download_from_AWS_s3(article.img_addr)

            except Exception as e:
                print(f"S3에서 이미지 다운로드 실패 {e}")

            if article.headline == 1:
                headline.append({
                "id": article.id,
                "url": article.url,
                "title": article.title,
                "content": article.content,
                "publisher": article.publisher,
                "reporter": article.reporter,
                "publish_date": article.publish_date.strftime('%Y-%m-%d'),
                "category": article.field,
                "image": img,
            })

            article_list.append({
                "id": article.id,
                "url": article.url,
                "title": article.title,
                "content": article.content,
                "publisher": article.publisher,
                "reporter": article.reporter,
                "publish_date": article.publish_date.strftime('%Y-%m-%d'),
                "category": article.field,
                "image": img,
            })


            

        return {
            "headline" : headline,
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
        active_topics = db.query(HotTopic).filter(HotTopic.activate == 1).all()
        topic_ids = [{'id':t.id,
                      'keyword':t.name}
                      for t in active_topics]


        return topic_ids


    finally:
        db.close()

#핫토픽 id로 기사들 찾아오기
def find_article_by_hottopicId(id):
    db = SessionLocal()
    try:
        articles = db.query(Bridge).filter(Bridge.hot_topics_id == id).all()
        # for i in articles:
        #     pass
        #     # print(i.hot_topics_id,i.articles_id)

        return len(articles)
    finally:
        db.close()




#핫토픽 파이프라인.
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

            print(len(summaries))

            # 5. 정치 성향별 그룹핑
            grouped_by_stance = {"진보": [], "중립": [], "보수": []}
            
            for summary in summaries:
                print(summary.id)
                stance = article_to_stance.get(summary.articles_id)
                
                print(f'#### stance : {stance}')
                # if stance not in grouped_by_stance:
                    # continue

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


#헤드라인 기사 찾아주는 라우터.
def get_headline_articles(limit: int = 8):
    db = SessionLocal()

    result = []
    articles = db.query(Article)\
        .filter(Article.headline == 1)\
        .order_by(Article.publish_date.desc())\
        .limit(limit)\
        .all()
    
    for article in articles:
        try:
            img = None
            if article.img_addr != "https://our-capstone06.s3.amazonaws.com/article_img/NoExistThumbnail.jpg":
                img = download_from_AWS_s3(article.img_addr)
        except Exception as e:
            print(f"S3에서 이미지 다운로드 실패 {e}")

        result.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "field" : article.field,
            "image": img,
            "publish_date": article.publish_date,
            "publisher": article.publisher,
            "url" : article.url
        })
        


    return result


def find_hottopic_detail_by_id(hot_topic_id: int, stance: str = None) -> dict | None:
    db = SessionLocal()
    try:
        # 🔍 키워드 이름 먼저 가져오기
        hot_topic = db.query(HotTopic).filter(HotTopic.id == hot_topic_id).first()
        if not hot_topic:
            return None

        keyword = hot_topic.name

        # 🔍 해당 핫토픽에 연결된 기사들 (Bridge 테이블 통해 연결되어 있다고 가정)

        query = (
            db.query(Article, ArticleSummary, Bridge)
            .join(Bridge, Bridge.articles_id == Article.id)
            .outerjoin(ArticleSummary, Article.id == ArticleSummary.articles_id)
            .filter(Bridge.hot_topics_id == hot_topic_id)
        )

        if stance:
            query = query.filter(Bridge.stance == stance)

        results = query.all()

        stance_data = defaultdict(lambda: defaultdict(list))  # {stance: {source: [articles]}}

        for article, summary, bridge in results:
            summary_text = summary.summary_text if summary else article.content[:100] + "..."
            stance_label = bridge.stance
            source = article.publisher

            stance_data[stance_label][source].append({
                "title": article.title,
                "summary": summary_text
            })

        if stance:
            # 단일 성향 요청
            sources = [
                {
                    "source": src,
                    "articles": arts
                } for src, arts in stance_data[stance].items()
            ]
            return {
                "keyword": keyword,
                "stance": stance,
                "sources": sources
            }
        else:
            # 전체 성향 요청
            formatted_stances = {}
            for stance_label, sources_dict in stance_data.items():
                formatted_stances[stance_label] = [
                    {
                        "source": src,
                        "articles": arts
                    } for src, arts in sources_dict.items()
                ]
            return {
                "keyword": keyword,
                "stances": formatted_stances
            }

    except Exception as e:
        print(f"[핫토픽 조회 오류] {e}")
        return None
    finally:
        db.close()


def find_analysis_by_hot_topic_id(hot_topic_id:int):
    db = SessionLocal()
    try:
        analysis = db.query(AnalysisSummary)\
                .filter(AnalysisSummary.hot_topics_id == hot_topic_id)\
                .order_by(AnalysisSummary.id.desc())\
                .first()


        return analysis.content

    except Exception as e:
        print(f"[핫토픽 조회 오류] {e}")
        return None
    finally:
        db.close()


def find_article_by_keyword(keyword: str, page: int = 1, per_page: int = 10):
    db = SessionLocal()
    try:
        offset = (page - 1) * per_page
        query = text("""
            SELECT * FROM articles
            WHERE MATCH(title, content) AGAINST(:keyword IN NATURAL LANGUAGE MODE)
            LIMIT :limit OFFSET :offset
        """)
        articles = db.execute(query, {
            "keyword": keyword,
            "limit": per_page,
            "offset": offset
            }).mappings().fetchall()
        total_articles = len(articles)

        article_list = []
        for article in articles:
            

            try:
                img = download_from_AWS_s3(article["img_addr"])
            except Exception as e:
                
                print(f"S3에서 이미지 다운로드 실패 {e}")

            article_list.append({
                "id": article["id"],
                "url": article["url"],
                "title": article["title"],
                "content": article["content"],
                "publisher": article["publisher"],
                "reporter": article["reporter"],
                "publish_date": article["publish_date"].strftime('%Y-%m-%d'),
                "image": img,
            })

            

        return {
            "articles": article_list,
            "current_page": page,
            "total_pages": (total_articles + per_page - 1) // per_page,
            "total_articles": total_articles,
        }

        
    except Exception as e:
        print(f"[Fulltext 검색 오류] {e}")
        return []
    finally:
        db.close()


