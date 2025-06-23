import os
from app.db.database import SessionLocal
import difflib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from app.db.models import ArticleSummary,Article,HotTopic,Bridge,AnalysisSummary

# 환경 변수 로드
load_dotenv()

DB_CONFIG = {
    'host' : "localhost",
    'user' : "root",
    'password' : "Msj46028759!",
    'database' : "naverapi"
}

SIMILARITY_THRESHOLD = 0.6
#press, title, link가 있는는 db에서 [input : press 1차 필터링, text_lines(ocr결과 한줄씩)로 2차 필터링(유사도로) output : link, title]
def get_article_by_press_and_lines_news_details(press, text_lines):
    """
    1) 주어진 언론사(press)에 해당하는 DB 기사만 가져옵니다.
    2) text_lines(텍스트 리스트)와 각 제목을 비교하여 가장 유사도가 높은 기사를 반환합니다.
    반환: (link, date, matched_title) 또는 None
    """
    try:
        db = SessionLocal()

        # 1차: 언론사 필터링

        results = db.query(Article).filter(Article.publisher == press).all()

        # query = "SELECT title, link FROM news_details WHERE press = %s"
        # cursor.execute(query, (press,))
        # results = cursor.fetchall()
        # cursor.close()
        # conn.close()

        if not results:
            print(f"❌ DB에 '{press}' 언론사의 기사가 없습니다.")
            return None

        # 2차: text_lines와 제목 비교
        best_match = None
        highest_sim = 0.0
        for row in results:
            candidate_title = row.title
            for line in text_lines:
                sim = difflib.SequenceMatcher(None, line, candidate_title).ratio()
                if sim > highest_sim:
                    highest_sim = sim
                    best_match = row

        

        print(f"✅ 최고 유사도: {highest_sim:.2f}")
        if best_match and highest_sim >= SIMILARITY_THRESHOLD:
            return best_match.url, best_match.title, best_match.publish_date
        else:
            print("⚠️ 유사한 제목을 찾지 못했습니다.")
            return None

    except Exception as e:
        print("MySQL 조회 실패:", e)
        return None
    
    finally:
        db.close()

#title, link, date가 있는는 db에서 확정된 제목으로 1차 필터링 output : link, date
# def get_article_url_by_title_fuzzy(ocr_title):
#     try:
#         conn = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="Msj46028759!",
#             database="naverapi"
#         )
#         cursor = conn.cursor(dictionary=True)

#         # 🔄 LIKE 없이 전체 제목 다 가져오기
#         query = "SELECT title, link, date FROM articles"
#         cursor.execute(query)
#         results = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         if not results:
#             print("❌ DB에 제목이 하나도 없어요.")
#             return None

#         # 🔍 OCR 제목과 가장 유사한 제목 찾기
#         best_match = None
#         highest_sim = 0.0
#         for row in results:
#             candidate_title = row["title"]
#             sim = difflib.SequenceMatcher(None, ocr_title, candidate_title).ratio()
#             if sim > highest_sim:
#                 highest_sim = sim
#                 best_match = row

#         print(f"✅ 최고 유사도: {highest_sim:.2f}")
#         if best_match and highest_sim > 0.6:  # 유사도 기준 임계값
#             return best_match["link"], best_match["date"]
#         else:
#             print("⚠️ 유사한 제목이 없어요.")
#             return None

#     except Exception as e:
#         print("MySQL 조회 실패:", e)
#         return None


def crawl_naver_news_article(url):
    """
    주어진 네이버 뉴스 URL에서 제목, 언론사, 본문 내용을 추출합니다.
    반환: dict {title, press, content} 또는 None
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 제목 추출
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"].strip() if title_tag else "제목 없음"

        # 언론사 추출
        press_tag = soup.find("meta", {"name": "twitter:creator"})
        press = press_tag["content"].strip() if press_tag else "언론사 정보 없음"

        # 본문 추출
        content_div = soup.select_one("article#dic_area")
        content = content_div.get_text(separator="\n", strip=True) if content_div else "본문 없음"

        return {"title": title, "press": press, "content": content}

    except Exception as e:
        print(f"❌ 기사 크롤링 실패: {url} / {e}")
        return None

def crawl_naver_news_article_url(url):
    """
    주어진 네이버 뉴스 URL에서
      • 제목(title)
      • 언론사(press)
      • 본문(content)
      • 작성일시(date: datetime)
    를 추출해 dict 로 반환합니다.
    실패 시 None 반환.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 제목
        title_tag = soup.find("meta", property="og:title")
        title = title_tag.get("content", "").strip() if title_tag else "제목 없음"

        # 언론사
        press_tag = soup.find("meta", {"name": "twitter:creator"})
        press = press_tag.get("content", "").strip() if press_tag else "언론사 정보 없음"

        # 본문
        content_div = soup.select_one("article#dic_area")
        content = content_div.get_text(separator="\n", strip=True) if content_div else "본문 없음"

        # 작성일시 파싱 (span._ARTICLE_DATE_TIME 의 data-date-time 속성)
        date = None
        dt_span = soup.select_one("span._ARTICLE_DATE_TIME")
        if dt_span and dt_span.has_attr("data-date-time"):
            dt_str = dt_span["data-date-time"].strip()  # 예: "2025-05-07 11:28:15"
            try:
                date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                date = None

        return {
            "title":   title,
            "press":   press,
            "content": content,
            "date":    date
        }

    except Exception as e:
        print(f"❌ 기사 크롤링 실패: {url} / {e}")
        return None
    

# 예시 호출
if __name__ == '__main__':
    # OCR/Extraction 단계에서 얻은 press와 text_lines
    press = '한국경제'
    text_lines = [
        "N 뉴스 엔터 스포츠 프리미엄",
        "정치 경제 사회 생활/문화 IT/과학 세계 랭킹",
        "한국경제 + 구독",
        "테슬라, 구글서 DOGE 검색 많을수록 주가 ‘타격’",
        "입력 2025.03.10. 오후 9:55",
        "수정 2025.03.10. 오후 10:09",
        "기사원문",
        "김정아 기자",
        "2 댓글",
        "DOGE가 테슬라의 새로운 위험 요소로 등장",
        "구글 검색에 머스크 정치 활동 리스크 반영",
        "이 기사는 국내 최대 해외 투자정보 플랫폼 한경 글로벌마켓에 게재된 기사입니다.",
        "JSK R",
        "UP TESLA",
        "TS NAKE NO CONFLICT SELL TESLA Your",
        "IS AGAIN SANE OF Not Your",
        "INTEREST (1)",
        "FUCK",
        "ELON",
        "DEPORT FUER moog",
        "“ECONOMIC",
        "COCCAPAE",
        "NECESSARY"
    ]

    result = get_article_by_press_and_lines_news_details(press, text_lines)
    print(result)
    if result:
        url, date = result
        print("📰 매칭된 URL:", url)
        print("🕒 작성시각:", date)

        # 크롤링으로 실제 기사 내용 추출
        article_info = crawl_naver_news_article(url)
        if article_info:
            print("\n=== 기사 정보 ===")
            print("📌 제목:", article_info["title"])
            print("🏢 언론사:", article_info["press"])
            print("📝 본문 내용:\n", article_info["content"])
        else:
            print("❌ 기사 정보를 가져오지 못했어요.")
    else:
        print("❌ 유사한 기사를 찾지 못했어요.")






