# 최신 방식 코드
from openai import OpenAI
from dotenv import load_dotenv
import os
key = os.getenv("open_ai_API_KEY")
client = OpenAI(api_key=key)

def summarize_with_chatgpt(article_text):
    prompt = f"""
다음은 뉴스 기사 본문입니다. 이를 간결하고 명확하게 요약해주세요.
줄글 형태가 아닌 **항목별 리스트 형식**으로 요약해 주세요.
각 항목은 1문장 이내로 작성하되, **원문에 있는 중요한 정보(인물, 날짜, 수치, 발언, 결정사항 등)**가 빠지지 않도록 꼭 포함해 주세요.
요약 항목은 최소 3개, 최대 6개로 작성해주세요.
"요약 불가" 같은 표현은 사용하지 마세요. 또한 max 토큰이 256이니 넘지 않도록 주의하세요.
기사:
{article_text}

[요약 리스트]
- 
"""
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "당신은 한국어 뉴스 요약 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=256, 
    )

    return response.choices[0].message.content.strip()



# 기사 입력 예시
sample_article = """
한덕수 대통령 권한대행 국무총리가 "온 국민의 마음을 하나로 모으고 정치·경제·사회 모든 분야에서 세계에 앞서가는 나라가 될 수 있기를 기대한다"고 말했습니다.
한 대행은 오늘(26일) 서울 종로구 4·19혁명기념도서관에서 열린 '제43회 4·19혁명 국가조찬기도회'에 보낸 축사를 통해 "4·19혁명으로 지켜낸 자유민주주의의 가치를 미래 세대에게 온전히 전해주기 위해 한층 더 성숙한 민주주의를 실현해 나가겠다"면서 이같이 밝혔습니다.
또 "우리의 민주주의 발전 경험을 억압받고, 고통받는 세계 시민과 함께 나누면서 존경받는 나라로 우뚝 서기를 소망한다"고 덧붙였습니다.
한 대행은 4·19혁명이 "대한민국을 넘어 세계 민주주의 역사에 하나의 이정표를 세운 우리의 빛나는 자긍심"이라며 "자유·민주·정의를 외쳤던 의로운 학생과 시민들의 숭고한 희생이 우리가 누리는 자유민주주의의 초석이 됐다"고 평가했습니다.
이어 지난 2023년 유네스코 세계기록유산에 등재된 4·19혁명의 기록물을 언급하며 "그날의 가르침을 높이 받들어 4·19 혁명의 정신을 소중히 지켜나가야 한다"고 밝혔습니다.
"정부는 우리 국민과 함께 4·19혁명을 기억하고, 유공자와 유가족분들에 대한 예우에 소홀함이 없도록 최선의 노력을 다하겠다"고도 강조했습니다.
"""

# # 요약 실행
# summary = summarize_with_chatgpt(sample_article)
# print("\n요약 결과:\n", summary)
# print("#")
# import json

# 예시 데이터 구조
summarized_data = {
    "진보": [
        {"original": "진보 기사 원문1", "summary": "요약1"},
        {"original": "진보 기사 원문2", "summary": "요약2"},
        {"original": "진보 기사 원문3", "summary": "요약3"}
    ],
    "중립": [
        {"original": "중립 기사 원문1", "summary": "요약1"},
        {"original": "중립 기사 원문2", "summary": "요약2"},
        {"original": "중립 기사 원문3", "summary": "요약3"}
    ],
    "보수": [
        {"original": "보수 기사 원문1", "summary": "요약1"},
        {"original": "보수 기사 원문2", "summary": "요약2"},
        {"original": "보수 기사 원문3", "summary": "요약3"}
    ]
}



# # 저장 경로
# output_path = "summarized_articles.json"

# # 파일 저장
# with open(output_path, "w", encoding="utf-8") as f:
#     json.dump(summarized_data, f, ensure_ascii=False, indent=2)


