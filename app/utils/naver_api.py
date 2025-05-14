import requests
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("API_KEY")
CLIENT_SECRET = os.getenv("API_SECRET")
SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"

HEADERS = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET
}

def search_news_by_keyword(keyword, max_per_keyword: int = 50) -> List[Dict]:
    results = []
    
    params = {
        "query": keyword["keyword"],
        "display": max_per_keyword,  # ← max_per_keyword 사용
        "sort": "sim"
    }
    response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    data = response.json()

    if "items" not in data:
        pass

    for item in data["items"]:

        link = item["link"]
        if not (link.startswith("https://n.news.naver.com/") or link.startswith("https://news.naver.com/")):
            continue

        results.append({
            "keyword": keyword,
            "link": item["link"],
            "pub_date": item["pubDate"]
        })
    return results

if __name__ == "__main__":
    # 🟡 여기서 키워드 리스트 넣어주면 돼요!
    keywords = ["인공지능", "경제", "스포츠"]

    # 🟠 결과 출력
    news_results = search_news_by_keyword(keywords)
    for news in news_results:
        print(news)