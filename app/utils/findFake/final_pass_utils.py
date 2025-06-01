import re
import os
from dotenv import load_dotenv
from app.utils.findFake.run_functions_gpt_fake import load_vectorstore, answer_with_gpt
from app.utils.findFake.naverAPI_news_time import 키워드_AND_쿼리_생성, 가장오래된_기사_역순
from app.utils.findFake.naverAPI_news_similar import count_articles_with_repetition
from app.utils.findFake.news_media_accuracy import compute_media_trust_penalty
from app.utils.findFake.run_functions_gpt_summary import summarize_with_chatgpt

load_dotenv()

def safe_ratio(numer, denom):
    return numer / denom if denom > 0 else 0

# ✅ LLM 판단 결과 파싱 함수
def parse_llm_output(gpt_output: str):
    llm_results = {}
    patterns = {
        "사실성": r"1\.\s*사실 확인 가능 여부\s*:\s*(.*)",
        "출처":   r"2\.\s*공식 출처 언급 여부\s*:\s*(.*)",
        "과장":   r"3\.\s*과장된 표현 여부\s*:\s*(.*)",
        "논리":   r"4\.\s*논리적 오류 여부\s*:\s*(.*)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, gpt_output)
        if match:
            value = match.group(1).strip().lower()
            value = re.split(r"[\-\u2013]", value)[0].strip()
            llm_results[key] = value
        else:
            llm_results[key] = "모호"
    return llm_results

# ✅ GPT 키워드 추출 함수
def extract_keywords_from_gpt_output(gpt_output: str):
    match = re.search(r"\[검색 키워드\](.*?)$", gpt_output, re.DOTALL)
    if match:
        lines = match.group(1).strip().split("\n")
        return [re.sub(r"^-", "", line).strip() for line in lines if line.startswith("-")]
    return []

# ✅ 위험도 점수 계산 함수
def calculate_risk_score(llm_results):
    def map_llm_response(field, resp):
        if field in ["출처", "사실성"]:
            if re.search(r"(없다|아니다)", resp): return 1.0
            elif re.search(r"(있다|그렇다)", resp): return 0.0
            else: return 0.5
        elif field in ["과장", "논리"]:
            if re.search(r"(없다|아니다)", resp): return 0.0
            elif re.search(r"(있다|그렇다)", resp): return 1.0
            else: return 0.5
        return 0.5

    weights = {
        "출처": 0.1,
        "사실성": 0.25,
        "논리": 0.25,
        "과장": 0.1,
        "연결성": 0.0,
    }

    llm_risk = (
        map_llm_response("출처", llm_results["출처"])   * weights["출처"] +
        map_llm_response("사실성", llm_results["사실성"]) * weights["사실성"] +
        map_llm_response("논리", llm_results["논리"])     * weights["논리"] +
        map_llm_response("과장", llm_results["과장"])     * weights["과장"]
    )
    return round(llm_risk, 4)

# ✅ 평가 메인 함수 (이제 dict 리턴)
def evaluate_article(title, content, 기사_작성시각, media):
    article = f"{content}"
    vectorstore = load_vectorstore()

    # 1) LLM 진단
    gpt_output = answer_with_gpt(vectorstore, title, 기사_작성시각, article, k=3, threshold=0.7)
    # 2) [검색 키워드] 이하를 제거한 순수 진단 텍스트만 gpt_output 으로 사용
    if "[검색 키워드]" in gpt_output:
        gpt_output_split = gpt_output.split("[검색 키워드]")[0].strip()
    else:
        gpt_output_split = gpt_output.strip()
    llm_results = parse_llm_output(gpt_output)
    keywords = extract_keywords_from_gpt_output(gpt_output)


    # 4) 기본 리스크 계산
    base_risk = calculate_risk_score(llm_results)

    # 5) 언론사 신뢰도 기반 페널티
    trust_score, risk_penalty = compute_media_trust_penalty(media, max_penalty=0.15)
    applied_penalty = risk_penalty

    # 6) 최초 확산 지점
    query = 키워드_AND_쿼리_생성(keywords)
    최초기사 = 가장오래된_기사_역순(query)
    print("최초기사 검색!!!!!\n")
    risk_boost = risk_penalty
    if 최초기사:
        최초시각 = 최초기사["작성시각"]
        시간차 = (기사_작성시각 - 최초시각).total_seconds() / 3600
        print(시간차)
        if base_risk >= 0.5 and 시간차 <= 6:
            risk_boost += 0.05
            earliest_info = "사전에 준비된 콘텐츠일 가능성 높음"
        else:
            earliest_info = "사전에 준비된 콘텐츠일 가능성 낮음"
    else:
        if base_risk >= 0.5:
            risk_boost += 0.05
            earliest_info = "사전에 준비된 콘텐츠일 가능성 높음"
        else:
            earliest_info = "사전에 준비된 콘텐츠일 가능성 낮음"

    print("반복확산 검색!!!!!\n")
    # 7) 반복 확산 패턴
    repetition_count = count_articles_with_repetition(
        query=키워드_AND_쿼리_생성(keywords),
        target_article=article,
        target_datetime = 기사_작성시각,
        display=10,
        max_results=100,
        surface_threshold=0.5,
        surface_ratio=0.5,
    )
    
    if base_risk >= 0.5 and repetition_count >= 5:
        risk_boost += 0.1
        repetition_info = "콘텐츠 복제, 매크로 가능성 높음"
    else:
        repetition_info = "콘텐츠 복제, 매크로 가능성 낮음"

    # 8) 최종 리스크
    final_risk = round(base_risk + risk_boost, 4)

    return {
        "final_risk":          final_risk,
        "gpt_output":          gpt_output_split,
        "risk_penalty":        applied_penalty,
        "earliest_diffusion":  earliest_info,
        "repetition_pattern":  repetition_info,
    }

def parse_gpt_output_to_items(gpt_output: str):
    """
    GPT 진단 결과 문자열을 파싱해
    [
      {"item": ..., "result": ..., "hasWarning": bool, "reason": ...},
      ...
    ]
    형태로 반환
    """
    pattern = re.compile(
        r"\d+\.\s*(.+?)\s*:\s*(있다|없다|그렇다|아니다)\s*\n(.*?)(?=\n\d+\.|\Z)",
        re.DOTALL
    )
    items = []
    for match in pattern.finditer(gpt_output):
        name = match.group(1).strip()
        result = match.group(2).strip()
        reason = match.group(3).strip().replace("\n", " ") + "\n"
        # 경고 로직 확장
        if name in ["사실 확인 가능 여부", "공식 출처 언급 여부"] and result in ["없다", "아니다"]:
            has_warning = True
        elif name in ["과장된 표현 여부", "논리적 오류 여부"] and result in ["있다", "그렇다"]:
            has_warning = True
        else:
            has_warning = False
        items.append({
            "item":      name,
            "result":    result,
            "hasWarning": has_warning,
            "reason":    reason
        })
    return items

def summarize_article(title: str, content: str) -> str:
    """
    제목과 본문을 받아 하나로 합친 뒤,
    계층적 불릿 리스트 형태로 재구성하여 반환합니다.
    """
    article_text = f"제목: {title}\n본문: {content}"
    return summarize_with_chatgpt(article_text)
