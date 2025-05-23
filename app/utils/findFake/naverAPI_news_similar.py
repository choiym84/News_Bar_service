import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re
import difflib
import time
import aiohttp
import asyncio
# ▶ 의미 유사도 계산용
from sentence_transformers import SentenceTransformer, util

# 환경 변수 로드
load_dotenv()
CLIENT_ID = os.getenv("API_KEY")
CLIENT_SECRET = os.getenv("API_SECRET")

# ----------------------------------------------------------------
# 0. 의미 임베딩 모델 로드 (스크립트 시작 시 한 번만)
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')


# 1. 네이버 뉴스 API를 통해 1부터 100까지 기사를 수집하는 함수 (display=10 기준)
def fetch_articles(query, display=10, max_results=100):
    articles = []
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    # 1부터 max_results까지 (display=10이면 1, 11, 21, …)
    for start in range(1, max_results + 1, display):
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": "date"  # 최신순 정렬
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            items = data.get("items", [])
            for item in items:
                # 각 기사에서 제목과 링크, pubDate 추출
                try:
                    pubDate = datetime.strptime(item["pubDate"], "%a, %d %b %Y %H:%M:%S +0900")
                except Exception as e:
                    pubDate = None
                title = BeautifulSoup(item["title"], "html.parser").text
                link = item["link"]
                articles.append({
                    "title": title,
                    "link": link,
                    "pubDate": pubDate
                })
        except Exception as e:
            print(f"❌ API 요청 실패 (start={start}): {e}")
        time.sleep(0.5)  # API rate limit 조정
    return articles

# 2. 각 기사 URL에서 본문 텍스트를 추출하는 함수 (간단한 추출)
def extract_article_text(url, timeout=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        content_div = soup.select_one("article#dic_area")
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        return text.strip()
    except Exception as e:
        print(f"❌ 본문 추출 실패: {url} / {e}")
        return ""

# 3. 문장 분할 함수 (간단한 정규식 사용)
def split_sentences(text):
    # 한글 문장은 마침표, 물음표, 느낌표, 줄바꿈 등으로 분리
    sentences = re.split(r"[.!?…\n]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

# 4. 두 문장 사이의 유사도 계산 (difflib 이용)
def sentence_similarity(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()

# 5a. 표면 유사도 지표 계산
def compute_surface_similarity(target_text, candidate_text, threshold=0.5):
    target_sentences = split_sentences(target_text)
    candidate_sentences = split_sentences(candidate_text)
    
    if not target_sentences or not candidate_sentences:
        return 0.0, 0.0  # 문장이 없으면 0 반환
    
    similar_count = 0
    similarity_scores = []
    
    # 각 대상 문장에 대해, 후보 기사에서 가장 높은 유사도 계산
    for ts in target_sentences:
        max_sim = 0.0
        for cs in candidate_sentences:
            sim = sentence_similarity(ts, cs)
            if sim > max_sim:
                max_sim = sim
        similarity_scores.append(max_sim)
        if max_sim >= threshold:
            similar_count += 1
    
    repetition_ratio = similar_count / len(target_sentences)
    # 유사도 평균: threshold 이상인 문장들만 평균 내기 (없으면 0)
    similar_scores = [score for score in similarity_scores if score >= threshold]
    avg_similarity = sum(similar_scores) / len(similar_scores) if similar_scores else 0.0
    return repetition_ratio, avg_similarity

# # 5b. 의미 유사도 계산 함수 추가
# def compute_semantic_similarity(target_text, candidate_text):
#     t_sents = split_sentences(target_text)
#     c_sents = split_sentences(candidate_text)
#     if not t_sents or not c_sents:
#         return 0.0
#     # 문장 임베딩
#     emb_t = semantic_model.encode(t_sents, convert_to_tensor=True)
#     emb_c = semantic_model.encode(c_sents, convert_to_tensor=True)
#     # 코사인 유사도 행렬
#     cos_sim = util.pytorch_cos_sim(emb_t, emb_c)
#     # 각 대상 문장별 최고 유사도만 뽑아서 평균
#     max_per_row = [row.max().item() for row in cos_sim]
#     return sum(max_per_row) / len(max_per_row)

# 6. 조건 만족 기사 카운트 함수 (표면 + 의미 유사도 모두 계산)
def count_articles_with_repetition(query,
                                    target_article,
                                    target_datetime,
                                    display=10,
                                    max_results=100,
                                    surface_threshold=0.5,
                                    surface_ratio=0.5,
                                    ):
    articles = fetch_articles(query, display=display, max_results=max_results)
    ratio_count = 0

    for art in articles:
        pub = art.get("pubDate")
        # pubDate가 없거나 target_datetime과 1일 이상 차이나면 스킵
        if not pub or pub > target_datetime or abs(pub - target_datetime) > timedelta(days=3):
            continue
        candidate_text = extract_article_text(art["link"])
        if not candidate_text:
            continue

        # 1) 표면 유사도
        ratio, avg_sim = compute_surface_similarity(target_article, candidate_text, threshold=surface_threshold)
        # 2) 의미 유사도
        # sem_sim = compute_semantic_similarity(target_article, candidate_text)


        # 예시 필터링: 표면 유사도 조건 AND 의미 유사도 조건
        if ratio > surface_ratio:
            ratio_count += 1
        # if ratio > surface_ratio and sem_sim > semantic_threshold:
        #     sem_count += 1
    return ratio_count

# 7. 키워드 토큰화 및 AND 쿼리 생성 (각 키워드를 단어 단위로 분해하여 AND 조건으로)
def 키워드_AND_쿼리_생성(키워드_리스트):
    토큰_리스트 = []
    for 키워드 in 키워드_리스트:
        단어들 = re.findall(r"[가-힣a-zA-Z0-9]+", 키워드)
        토큰_리스트.extend(단어들)
    토큰_리스트 = sorted(set(토큰_리스트))
    query = " ".join(토큰_리스트)
    return query



# 8. 메인 실행: 대상 기사와 네이버 뉴스 검색 결과 기사 비교
if __name__ == "__main__":
    target_datetime = datetime.strptime("2025-04-07 14:18:00", "%Y-%m-%d %H:%M:%S")
    # 예시 키워드 리스트
    키워드_리스트 = [
        "우원식 국회의장",
        "김동연 경기지사",
        "개헌 국민투표"
    ]
    query = 키워드_AND_쿼리_생성(키워드_리스트)
    # 대상 기사 (비교할 기사)
    article = """
    우원식 국회의장이 대통령 선거일에 맞춰 개헌 국민투표를 함께 하자고 제안한 데 대해, 진보 진영 대권주자인 김동연 경기지사가 "개헌은 새로운 대한민국으로 가는 관문이 될 것"이라며 적극 동의한다는 뜻을 밝혔습니다.

    김 지사는 페이스북에 "윤석열 파면과 내란 종식은 끝이 아니라 시작이고, 새로운 7공화국 문을 열어야 한다"며, "계엄을 할 수 없도록 만드는 개헌과 경제 개헌, 분권형 4년 중임제를 비롯해, 대선과 총선 임기를 일치시키기 위한 대통령 3년 임기 단축도 자신이 줄곧 주장해 왔다"고 적었습니다.

    이어 "선거가 끝나면 대선 공약이 흐지부지되는 역사가 반복돼선 안 된다"며 "분권형 4년 중임제 등 공감대가 큰 사안은 대선과 동시 투표하고, 국민적 동의가 더 필요한 부분은 대선 공약을 통해 단계적으로 추진해야 한다"고 말했습니다.
    """
    print("== 네이버 API + 표면/의미 유사도 분석 시작 ==")
    cnt, s_cnt = count_articles_with_repetition(
        query,
        target_article=article,
        target_datetime=target_datetime,
        display=10,
        max_results=100,
        surface_threshold=0.5,
        surface_ratio=0.5,
    )
    print(f"\n✅ 조건 만족 기사 수: {cnt}")