import logging
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from typing import List, Dict, Optional

import re
from konlpy.tag import Okt

okt = Okt()

def clean_article_content(content: str) -> str:
    # 불필요한 이미지 설명, 기자 이름, 출처 등 제거
    patterns = [
        r'\[?사진[^\n]{0,30}?\]?',           # [사진], 사진제공 등
        r'사진\s*=\s*[^,\n]+',
        r'자료사진',
        r'[가-힣]{2,10}\s*기자',
        r'[가-힣]+\s*/\s*[가-힣]+(?:뉴스|일보)',
        r'촬영\s*=\s*[^\n]+',
        r'[가-힣]{2,10}\s*입장하고 있다'
    ]
    for pattern in patterns:
        content = re.sub(pattern, '', content)
    return content.strip()

def is_meaningful_article(content: str, min_length: int = 300, min_nouns: int = 20) -> bool:
    if len(content) < min_length:
        return False
    nouns = okt.nouns(content)
    return len(nouns) >= min_nouns


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 본문 파싱 함수 (공통으로 사용)
def parse_article(html: str) -> Dict[str, Optional[str]]:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.select_one("h2#title_area > span")
    title = title_tag.get_text(separator="\n", strip=True) if title_tag else ""

    # 본문 파싱 전 img_desc 제거
    for em in soup.select("em.img_desc"):
        em.decompose()  # DOM에서 해당 요소 완전히 제거
    
    #동영상이 있는 뉴스를 걸러야 할 듯...

    # soup.find("class.vod_player_wrap _VIDEO_AREA_WRAP")

    image_url = None
    if soup.select_one("img#img1"):
        image_url = soup.select_one("img#img1").get("data-src")

    content_tag = soup.select_one("article#dic_area")
    content = content_tag.get_text(separator="\n", strip=True) if content_tag else ""

    publisher_tag = soup.find("meta", attrs={"name": "twitter:creator"})
    publisher = publisher_tag["content"].strip() if publisher_tag else "언론사 정보 없음"

    reporter_tag = soup.find("em", class_="media_end_head_journalist_name")
    reporter = reporter_tag.text.strip().replace(" 기자", "") if reporter_tag else "기자 정보 없음"

    return {
        "title" : title,
        "content": content,
        "publisher": publisher,
        "reporter": reporter,
        "img_url": image_url
    }

# 개별 기사 크롤링 (비동기)
async def fetch_article_body(session: aiohttp.ClientSession, link: str) -> Optional[Dict[str, str]]:
    try:
        async with session.get(link) as response:
            if response.status == 200:
                html = await response.text()
                
                parsed_data = parse_article(html)
                parsed_data["link"] = link
                
                return parsed_data
            elif response.status == 404:
                logging.warning(f"404 Not Found: {link}")
            else:
                logging.warning(f"Error {response.status} fetching {link}")
    except Exception as e:
        logging.error(f"Error fetching {link}: {str(e)}")
    return None

# 메인 함수 (링크 리스트 → 결과 리스트)
async def crawl_articles(links: List[str]) -> List[Dict[str, str]]:
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_article_body(session, link) for link in links]
        articles = await asyncio.gather(*tasks)


    articles = [a for a in articles if a]

    # 링크를 기준으로 딕셔너리 생성
    crawled_dict = {article["link"]: article for article in articles}

    # 원래 링크 순서대로 정렬
    ordered_articles = [crawled_dict[link] for link in links if link in crawled_dict]

    result = []
    for i in ordered_articles:
        k = i['content']
        k = clean_article_content(k)

        if is_meaningful_article(k):
            i['content'] = k
            result.append(i)


    return result
    
