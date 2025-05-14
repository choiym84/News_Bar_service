import torch
from transformers import AutoTokenizer, pipeline
import torch
from transformers import AutoTokenizer, pipeline
import json
import re
from dotenv import load_dotenv
import os

# GEMMA 모델 로드
model_name = os.getenv("gemma_model_name")
api_token = os.getenv("gemma_api_token")

gemma_pipe = pipeline(
    "text-generation",
    model=model_name,
    device="cpu",
    torch_dtype=torch.bfloat16,
    token=api_token
)
tokenizer = AutoTokenizer.from_pretrained(model_name, token=api_token)


# 키워드 추출 함수
def extract_keywords_from_response(text: str):
    # 숫자 목록 형태에서 키워드만 추출 (예: 1. 한덕수 출마)
    lines = text.strip().splitlines()
    keywords = []
    for line in lines:
        match = re.match(r"\d+\.\s*(.+)", line)
        if match:
            keywords.append(match.group(1).strip())
    return keywords

# # JSON 저장 함수
# def save_keywords_to_json(keywords, filename="political_keywords.json"):
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump({"keywords": keywords}, f, ensure_ascii=False, indent=2)
#     print(f">>> 키워드가 {filename} 에 저장되었습니다.")

# 뉴스 헤드라인
headlines = [
    "북·러, 북한군 러 파병 잇단 인정…김정은 방러 ‘빌드업’ 시작했나",
    "홍준표 “탄핵 정권 총리, 대선 출마 맞나”면서 “단일화는 해야”",
    "이재명 42% 단독 질주…한덕수 출마해도 범보수 합쳐 41%",
    "이재명 대통령은 국민을 크게 통합하는 우두머리",
    "[속보] 한덕수, 5월 1일 사퇴…2일 '대선 출마선언'",
    "이재명의 '광폭 우클릭'…보수책사 영입하고 이승만·박정희 묘역 참배",
    "'이회창 책사' 윤여준 영입한 이재명... 상임 선대위원장",
    "반도체 5.5兆 지원시 7.2兆 경제효과…적기 보조금 절실",
    "홍준표 “한덕수 불출마하면 오히려 우리 입장 곤란”",
    "외교부, 대선 전 재외공관장 9명 인사 발표…김대기·방문규는 제외"
]
headlines_text = "\n".join(headlines)

# 프롬프트
prompt = f"""
다음은 정치 뉴스 헤드라인들이다.
이 헤드라인들을 바탕으로,
**뉴스 검색 시 활용 가능한 핵심 정치 주제 키워드 6개**를 추출해줘.

요구사항:
- 각 키워드는 **해당 정치 이슈를 대표하는 핵심 표현**이어야 해.
- **인물명 + 행위** 또는 **정치사건 중심 표현** 형태가 좋음 
- **추상적이거나 일반적인 단어는 피하고, 구체적이고 검색 가능한 형태로.
- **설명은 빼고**, 키워드만 **1~6번 형태로 출력**해줘.
- 키워드는 **서로 겹치지 않도록**, 서로 다른 이슈를 최대한 커버해줘.

헤드라인:
{headlines_text}

키워드만 1~6번으로 출력해줘.
"""


# 생성 함수 정의
def generate_responses(prompt, num_samples=1):
    responses = []
    for _ in range(num_samples):
        out = gemma_pipe(prompt, max_new_tokens=1000, do_sample=True, temperature=0.7)
        print("=== 원본 출력 확인 ===")
        print(out)  # 출력 형태 확인
        responses.append(out[0])
        generated_text = responses[0]["generated_text"]
        keywords = extract_keywords_from_response(generated_text)
    return keywords




