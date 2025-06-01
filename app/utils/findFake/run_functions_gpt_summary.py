# 최신 방식 코드
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("open_ai_API_KEY"))

def summarize_with_chatgpt(original_text: str) -> str:
    system_prompt = """
당신은 한국어 뉴스 요약 및 구조화 전문가입니다.
주어진 텍스트에서 소제목과 그에 속하는 세부항목을 자동으로 감지한 뒤,
아래 형식의 계층적 불릿 리스트로 재구성하세요.

• 소제목 A:
  • 세부항목 1
  • 세부항목 2
  …

• 소제목 B:
  • 세부항목 1
  …

- 소제목 앞에는 • 한 칸, 소제목 뒤에 콜론(:)을 붙입니다.
- 소제목 아래 세부항목은 두 칸 들여쓰기 후 • 한 칸으로 표기합니다.
- 불릿 기호는 모두 “•” 로 통일합니다.
"""
    user_prompt = f"다음 원본 내용을 위 포맷으로 정리해줘:\n\n{original_text}"

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system",  "content": system_prompt.strip()},
            {"role": "user",    "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()

def summarize_article(title: str, content: str) -> str:
    """
    제목과 본문을 하나로 합친 뒤,
    계층적 불릿 리스트 형태로 재구성하여 반환합니다.
    """
    article_text = f"제목: {title}\n본문: {content}"
    return summarize_with_chatgpt(article_text)

if __name__ == "__main__":
    # 기사 입력 예시
    sample_article = """
    한덕수 대통령 권한대행 국무총리가 "온 국민의 마음을 하나로 모으고 정치·경제·사회 모든 분야에서 세계에 앞서가는 나라가 될 수 있기를 기대한다"고 말했습니다.
    한 대행은 오늘(26일) 서울 종로구 4·19혁명기념도서관에서 열린 '제43회 4·19혁명 국가조찬기도회'에 보낸 축사를 통해 "4·19혁명으로 지켜낸 자유민주주의의 가치를 미래 세대에게 온전히 전해주기 위해 한층 더 성숙한 민주주의를 실현해 나가겠다"면서 이같이 밝혔습니다.
    또 "우리의 민주주의 발전 경험을 억압받고, 고통받는 세계 시민과 함께 나누면서 존경받는 나라로 우뚝 서기를 소망한다"고 덧붙였습니다.
    한 대행은 4·19혁명이 "대한민국을 넘어 세계 민주주의 역사에 하나의 이정표를 세운 우리의 빛나는 자긍심"이라며 "자유·민주·정의를 외쳤던 의로운 학생과 시민들의 숭고한 희생이 우리가 누리는 자유민주주의의 초석이 됐다"고 평가했습니다.
    이어 지난 2023년 유네스코 세계기록유산에 등재된 4·19혁명의 기록물을 언급하며 "그날의 가르침을 높이 받들어 4·19 혁명의 정신을 소중히 지켜나가야 한다"고 밝혔습니다.
    "정부는 우리 국민과 함께 4·19혁명을 기억하고, 유공자와 유가족분들에 대한 예우에 소홀함이 없도록 최선의 노력을 다하겠다"고도 강조했습니다.
    """

    # 요약 실행
    summary = summarize_with_chatgpt(sample_article)
    print("\n요약 결과:\n", summary)