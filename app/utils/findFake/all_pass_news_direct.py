import re
import os
from datetime import datetime
from dotenv import load_dotenv
from app.utils.findFake.run_functions_gpt_fake import load_vectorstore, answer_with_gpt
from app.utils.findFake.naverAPI_news_time import 키워드_AND_쿼리_생성, 가장오래된_기사_역순
from app.utils.findFake.naverAPI_news_similar import count_articles_with_repetition  # 🔁 반복 패턴 모듈 추가
from app.utils.findFake.news_media_accuracy import compute_media_trust_penalty

# ✅ LLM 판단 결과 파싱 함수
def parse_llm_output(gpt_output: str):
    llm_results = {}
    patterns = {
        "사실성": r"1\.\s*사실 확인 가능 여부\s*:\s*(.*)",
        "출처": r"2\.\s*공식 출처 언급 여부\s*:\s*(.*)",
        "과장": r"3\.\s*과장된 표현 여부\s*:\s*(.*)",
        "논리": r"4\.\s*논리적 오류 여부\s*:\s*(.*)",
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
        keywords = [re.sub(r"^-", "", line).strip() for line in lines if line.startswith("-")]
        return keywords
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
        else:
            return 0.5

    weights = {                                 ####여기가 가중치
        "출처": 0.1,
        "사실성": 0.25,
        "논리": 0.25,
        "과장": 0.1,
        "연결성": 0.0,
    }

    llm_risk = (
        map_llm_response("출처", llm_results["출처"]) * weights["출처"] +
        map_llm_response("사실성", llm_results["사실성"]) * weights["사실성"] +
        map_llm_response("논리", llm_results["논리"]) * weights["논리"] +
        map_llm_response("과장", llm_results["과장"]) * weights["과장"]
    )

    return round(llm_risk, 4)

# ✅ 평가 메인 함수
def evaluate_article(title, content, 기사_작성시각, media):
    article = f"{title}\n\n{content}"
    vectorstore = load_vectorstore()

    # Step 1: GPT 판단 및 파싱
    gpt_output = answer_with_gpt(vectorstore, title, article, k=3, threshold=0.7)
    llm_results = parse_llm_output(gpt_output)
    keywords = extract_keywords_from_gpt_output(gpt_output)

    # Step 3: 기본 선행 위험도 계산
    base_risk = calculate_risk_score(llm_results)

    # Step 4: 최초 기사 기반 후처리
    query = 키워드_AND_쿼리_생성(keywords)
    최초기사 = 가장오래된_기사_역순(query)
    risk_boost = 0.0
    
    
    trust_score, risk_penalty = compute_media_trust_penalty(media, max_penalty=0.15)          ####여기가 조건부
    risk_boost += risk_penalty
    
    
    if 최초기사:
        최초시각 = 최초기사["작성시각"]
        시간차 = (기사_작성시각 - 최초시각).total_seconds() / 3600          ####여기가 조건부
        if base_risk >= 0.5 and 시간차 <= 48:
            risk_boost += 0.05
    else :
        if base_risk >= 0.5:
            risk_boost += 0.05

    # Step 5: 반복 확산 기사 수 확인
    repetition_count = count_articles_with_repetition(
        query=키워드_AND_쿼리_생성(keywords),
        target_article=article,
        target_datetime = 기사_작성시각,
        display=10,
        max_results=100,
        surface_threshold=0.5,
        surface_ratio=0.5,
    )
    
    if repetition_count >= 5:            ####여기가 조건부
        risk_boost += 0.1

    final_risk = round(base_risk + risk_boost, 4)
	
    return final_risk

# ✅ 테스트 실행 예시
if __name__ == "__main__":
    title = "\"장시간 노동, 이제 그만\"…주4.5일제가 온다"
    date = datetime.strptime("2025-05-20 22:11:00", "%Y-%m-%d %H:%M:%S")
    media = "KBS"

    content = """2023년 기준 국내 노동자의 연간 노동시간은 무려 2,500시간에 달하며, 이는 전 세계 최악 수준으로 평가받고 있습니다.
독일보다 800시간 이상 더 일하는 셈이며, 이로 인해 국내 노동자 1,000명 이상이 매년 과로로 사망에 이른다는 충격적인 보고가 있습니다.

[익명의 산업의학 전문의 : “이런 근로 환경은 노동자가 아니라 노예에 가깝습니다. 정부는 사실상 방관하고 있습니다.”]

실제로, 하루 12시간 노동은 이제 한국에서 표준처럼 여겨지고 있으며, 세계보건기구(WHO)의 경고를 넘어선 상황입니다.

국민의힘 김문수 후보는 “4.5일제는 대한민국의 경쟁력을 갉아먹는 좌파적 발상”이라며, 주 6일 근무 유지를 공식화했습니다. 이에 대해 노동계는 “국민을 착취하려는 시대착오적 망언”이라며 강하게 반발하고 있습니다.

현실은 더욱 심각합니다. 중소기업 노동자 다수는 주 60시간 이상 근무하고도 최저임금조차 받지 못하며, 인권 침해 수준의 노동이 강요되고 있다는 증언이 잇따르고 있습니다.

[자영업자 A씨 : “우리 같은 사람은 죽어도 언론에 안 나옵니다. 정부는 아예 신경도 안 써요.”]

정부와 기업은 공범이라는 비판 속에서, 주 4일제는커녕 기본적인 노동권조차 지켜지지 않는 실정입니다.
    """

        
    
    evaluate_article(title, content, date, media)