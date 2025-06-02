## GPT 버전
import os
import json
import re
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("open_ai_API_KEY"))

def extract_keywords_from_response(text: str):
    lines = text.strip().splitlines()
    keywords = []
    for line in lines:
        match = re.match(r"\d+\.\s*(.+)", line)
        if match:
            keywords.append(match.group(1).strip())
    return keywords

def save_keywords_to_json(keywords, filename="political_keywords_gpt.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"keywords": keywords}, f, ensure_ascii=False, indent=2)
    print(f">>> 키워드가 {filename} 에 저장되었습니다.")

def get_political_keywords_from_headlines(headlines: list[str], save_to_file=False) -> list[str]:
    headlines_text = "\n".join(headlines)
    prompt = f"""
다음은 정치 뉴스 헤드라인들이다.
이 헤드라인들을 바탕으로, **뉴스 검색 시 활용할 수 있는 핵심 정치 키워드 6개**를 뽑아줘.

요구사항:
- 각 키워드는 **해당 이슈를 대표하는 핵심 주제어**여야 해.
- **3단어 이내**의 짧은 문구로,
  - 예: "'홍준표' 한덕수 지지", "대통령경호처 쇄신", "이재명 평화"
- 가능한 형식:
  - **인물명 + 행위/태도/전략**
  - **사건/조직 + 변화/갈등**
  - **정당 + 전략/평가**
- **설명, 논평은 금지**. 키워드만 출력.
- **중복된 주제 없이**, 다른 이슈 6개를 다양하게 뽑아줘.
- 아래처럼 **번호 매기기 형식(1. ~ 6.)**으로 출력해.

헤드라인:
{headlines_text}

키워드만 1~6번으로 출력해줘.
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 정치 헤드라인에서 핵심 키워드를 잘 뽑는 AI야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    output_text = response.choices[0].message.content.strip()
    keywords = extract_keywords_from_response(output_text)
    

    if save_to_file:
        save_keywords_to_json(keywords)

    return keywords

