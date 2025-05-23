import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv
import re

# ✅ 환경 변수 로드
load_dotenv()
CLIENT_ID = os.getenv("API_KEY")
CLIENT_SECRET = os.getenv("API_SECRET")

def 키워드_AND_쿼리_생성(키워드_리스트):
    토큰_리스트 = []
    for 키워드 in 키워드_리스트:
        # 한글/영어/숫자 기준 단어 추출
        단어들 = re.findall(r"[가-힣a-zA-Z0-9]+", 키워드)
        토큰_리스트.extend(단어들)

    # 중복 제거 및 정렬(optional)
    토큰_리스트 = sorted(set(토큰_리스트))

    # AND 쿼리 생성
    query = " ".join(토큰_리스트)
    return query

# 키워드_리스트 = [
#     "우원식 국회의장",
#     "김동연 경기지사",
#     "개헌 국민투표"
# ]



def 가장오래된_기사_역순(query, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }

    for start in reversed(range(1, 92, display)):  # 91 → 1
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        items = data.get("items", [])

        if not items:
            continue  # 다음 페이지로 넘어감

        # 가장 오래된 기사 추출 (이 페이지에서만)
        가장오래된_시각 = None
        가장오래된_기사 = None
        for item in items:
            try:
                pubDate = datetime.strptime(item["pubDate"], "%a, %d %b %Y %H:%M:%S +0900")
                제목 = BeautifulSoup(item["title"], "html.parser").text
                링크 = item["link"]
                if (가장오래된_시각 is None) or (pubDate < 가장오래된_시각):
                    가장오래된_시각 = pubDate
                    가장오래된_기사 = {
                        "작성시각": pubDate,
                        "기사_제목": 제목,
                        "기사_링크": 링크
                    }
            except:
                continue

        if 가장오래된_기사:
            return 가장오래된_기사  # ✅ 가장 최근 페이지에서 가장 오래된 기사 찾음

    print("❌ 관련된 기사를 찾을 수 없습니다.")
    return None

if __name__ == "__main__":
    # ✅ 실행
    키워드_리스트 = ['산불 대응 중앙지방안전대체법원', '재난안전특권세', '경북·경남 산불']

    query = 키워드_AND_쿼리_생성(키워드_리스트)
    가장오래된_기사_결과 = 가장오래된_기사_역순(query)
    if 가장오래된_기사_결과:
        print("📌 가장 오래된 기사")
        print("🕒 작성 시각:", 가장오래된_기사_결과["작성시각"])
        print("📰 제목:", 가장오래된_기사_결과["기사_제목"])
        print("🔗 링크:", 가장오래된_기사_결과["기사_링크"])
    else:
        print("❌ 관련 기사를 찾을 수 없습니다.")
    
    
    
# from datetime import timedelta

# # 예시 입력
# 위험도 = 0.78
# 내_기사_작성시각 = datetime.strptime("2025-04-01 14:00:00", "%Y-%m-%d %H:%M:%S")  # 이부분은 LLM에서 가져오기
# 최초_기사_시각 = 가장오래된_기사_결과["작성시각"]
# 공식_보도자료_시각 = None  # 또는 datetime 객체로 지정 #이부분은 RAG가져올때 Chroma에서 뽑아오기

# # ✅ 기준 시각 설정
# if 공식_보도자료_시각:
#     기준시각 = 공식_보도자료_시각
# elif 최초_기사_시각:
#     기준시각 = 최초_기사_시각
# else:
#     기준시각 = None  # 이슈 시점 미정

# # ✅ 이슈 직후 여부 판단 (예: 기준시각 ± 1시간 안이면 직후로 간주)
# 최초_확산_시점 = "판단불가"
# if 기준시각:
#     if abs((내_기사_작성시각 - 기준시각).total_seconds()) <= 3600:
#         최초_확산_시점 = "이슈 직후"
#     else:
#         최초_확산_시점 = "시간 차이 존재"

# # ✅ 위험도 보정
# if 위험도 > 0.7 and 최초_확산_시점 == "이슈 직후":
#     위험도 += 0.05  # 보조 점수 추가

# # ✅ 출력 결과 확인
# print(f"🧠 기준시각: {기준시각}")
# print(f"📌 최초 확산 시점: {최초_확산_시점}")
# print(f"⚠️ 최종 위험도: {위험도:.2f}")