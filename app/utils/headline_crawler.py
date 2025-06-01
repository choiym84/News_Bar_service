import requests
from bs4 import BeautifulSoup
from typing import List, Dict

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def request_html(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # 요청 실패 시 예외 발생
    return BeautifulSoup(response.text, "html.parser")

def get_naver_headlines(section_url: str = "https://news.naver.com/section/100", limit: int = 10) -> List[Dict[str, str]]:
    soup = request_html(section_url)
    articles = soup.select('li.sa_item._SECTION_HEADLINE')

    headlines = []
    for article in articles[:limit]:
        title_tag = article.select_one('strong.sa_text_strong')
        link_tag = article.select_one('a')
        link_high = article.select_one('span.sa_text_cluster_num').text
        
    
        if not title_tag or not link_tag:
            continue

        headlines.append({
            "title": title_tag.text.strip(),
            "link": link_tag['href'],
            "best" : link_high
        })
        
    return headlines

# for i in get_naver_headlines():
#     print(i["title"])

