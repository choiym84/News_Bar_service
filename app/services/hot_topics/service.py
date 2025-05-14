from app.utils.headline_crawler import get_naver_headlines
from app.utils.naver_api import search_news_by_keyword
from app.utils.content_crawler import crawl_articles
from typing import List, Dict

# 더미 1차 모델 (나중에 AI 서버 연결 예정)
def extract_dummy_keywords(titles: List[str]) -> List[str]:
    # 실제로는 모델 서버에 POST 요청해야 할 자리
    #############################
    # 1차 AI 모델 추가
    #
    #############################
    return ["연금개혁", "부동산", "총기소지", "대통령 시위", "헌법재판"]

async def collect_hot_topics_step1():
    headlines = get_naver_headlines()  # 10개 제목 크롤링
    titles = [item["title"] for item in headlines]
    keywords = extract_dummy_keywords(titles)

    return {
        "headlines": headlines,
        "keywords": keywords
    }


async def collect_hot_topics_step2(keywords: List[str]):
    articles = await search_news_by_keyword(keywords)
    return {"articles": articles}


async def collect_hot_topics_step3(articles: List[Dict]):
    detailed_articles = await crawl_articles(articles)
    return {"articles": detailed_articles}