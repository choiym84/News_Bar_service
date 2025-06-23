import re
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
key = os.getenv("open_ai_API_KEY")
client = OpenAI(api_key=key)  # 실제 키로 교체

def compare_political_orientations_gpt_json(
        progressive_articles: list[str],
        neutral_articles: list[str],
        conservative_articles: list[str],
        keyword: str
) -> dict:
    j = "\n\n--- 진보 기사 ---\n" + "\n\n".join(progressive_articles)
    n = "\n\n--- 중립 기사 ---\n" + "\n\n".join(neutral_articles)
    b = "\n\n--- 보수 기사 ---\n" + "\n\n".join(conservative_articles)

    prompt = f"""
다음은 진보/중립/보수 성향의 기사 내용입니다:

[진보 기사]
{j}

[중립 기사]
{n}

[보수 기사]
{b}

그리고 아래는 이번 비교 분석에서 중심이 되는 주요 주제 키워드입니다:
{keyword}

---

위 기사와 키워드를 바탕으로, 다음의 두 가지 구성으로 내용을 요약하되 **정확한 JSON 구조**로 출력해 주세요.

1. 먼저, 정치 성향별 전체 요약을 각각 1줄로 작성해 주세요 (기사 흐름 기준으로):

2. 다음으로, 기사들에서 공통적으로 다루는 주요 비교 카테고리 주요 키워드를 고려하여 2~4개 도출하고, 각 카테고리마다 정치 성향별 관점을 각각 1줄로 요약해 주세요. 각 성향의 관점을 대립적으로 요약해주세요.

3. 각 요약을 최대 16글자 정도로 뽑아주고 정말 불필요한 어미나 관용어구 다 빼고 핵심만 전달해줘.

---

출력은 아래 예시와 같은 **JSON 구조**로 해 주세요:

{{
  "1. 전체 요약": {{
    "진보": "여기에 진보 요약",
    "중립": "여기에 중립 요약",
    "보수": "여기에 보수 요약"
  }},
  "2. 관점별 주요 비교 카테고리": {{
    "카테고리1": {{
      "진보": "카테고리1에 대한 진보 관점",
      "중립": "카테고리1에 대한 중립 관점",
      "보수": "카테고리1에 대한 보수 관점"
    }},
    "카테고리2": {{
      "진보": "...",
      "중립": "...",
      "보수": "..."
    }}
  }}
}}

주의사항:
- 모든 요약 문장은 반드시 1줄 이내로 작성
- 과도한 해석 없이 기사 내 표현 중심으로 요약
- 표 형식이나 리스트 없이, 반드시 위 JSON 형식으로 출력
"""



    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "너는 정치기사를 잘 비교 분석하는 AI야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    output = response.choices[0].message.content.strip()
    

    return parse_gpt_output_to_json(output)


import re

def parse_gpt_output_to_json(text: str) -> dict:
    try:
        # 백틱, 공백, 개행 제거
        cleaned = text.strip().strip("`")
        
        # JSON 파싱
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        print("⚠️ JSON 파싱 실패:", e)
        return {}



prog = [
    "경단체와 진보 성향 국회의원들은 “탄소세는 온실가스 감축뿐 아니라 사회적 불평등을 완화하는 도구”라며, 저소득층·취약 계층을 위한 보전 대책을 포함한 패키지 법안을 조속히 처리해야 한다고 촉구했다.",
    "정부 여당은 탄소세로 걷힌 세수를 지역 공공교통·신재생에너지 보조금으로 전환해 “국민 모두가 깨끗한 에너지 혜택을 누릴 수 있게 할 것”이라고 밝혔다. 이를 통해 일자리 창출과 지역 균형 발전을 동시에 도모한다는 계획이다.",
    "프랑스·스웨덴 등에서 탄소세 도입 후 대체에너지 산업 고용이 15% 늘어난 것을 들며, “한국도 적정 수준의 탄소세를 통해 그린 일자리를 늘려야 기후 위기에 선제 대응할 수 있다”고 전문가들이 제언했다.",
]
neut = [
    "환경부는 2030년 GHG 감축 목표 달성을 위해 탄소세 도입을 검토 중이다. 반면 산업계는 “국제 경쟁력 약화 우려”를, 시민단체는 “기후 위기 대응 필수”를 각각 강조하며 논의가 팽팽하게 맞서고 있다.",
    "국회 환경노동위원회 소속 의원들이 발표한 탄소세 초안에 따르면, 1톤당 3만원 수준에서 시작해 5년간 연 1만원씩 인상하는 방안이 제시됐다. 시행 첫해엔 발전부문, 3년차부터 제조업 전반으로 확대하는 로드맵도 포함됐다.",
    "한국환경정책학회와 경제연구소가 공동 실시한 설문조사에서, 탄소세 도입 시 단기 GDP 성장률이 0.2%포인트 하락할 수 있으나 2030년까지 온실가스 배출량이 10%가량 줄어들 것이라는 전망이 나왔다.",
]
cons = [
    "재계는 “탄소세가 도입되면 에너지 비용이 급증해 중소·중견기업의 경쟁력이 떨어질 것”이라며, 도입 시점과 세율 수준을 더욱 신중히 조정해야 한다고 촉구했다.",
    "농업·화물 운송업계는 “온실가스 배출량이 많은 업종임에도 보전 장치가 없으면 농가·운수업체 생존이 위협받는다”며, 도입 전 충분한 감면·보조금 대책 없이는 현실성이 떨어진다고 반발했다.",
    "일부 경제 전문가들은 “탄소세를 매기기보다 R&D 세액공제·친환경 기술 개발 지원을 통해 시장 자율적으로 배출을 줄이는 편이 효과적”이라며 정부 지원 방향 전환을 제안했다.",
]
# result_json = compare_political_orientations_gpt_json(prog, neut, cons)
# import json
# # 결과 출력
# #print(json.dumps(result_json, ensure_ascii=False, indent=2))

# # 결과 저장
# with open("comparison_result.json", "w", encoding="utf-8") as f:
#     json.dump(result_json, f, ensure_ascii=False, indent=2)
