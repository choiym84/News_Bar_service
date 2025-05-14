import re

from openai import OpenAI
from dotenv import load_dotenv
import os
key = os.getenv("open_ai_API_KEY")
client = OpenAI(api_key=key)  # 실제 키로 교체

def compare_political_orientations_gpt_json(
        progressive_articles: list[str],
        neutral_articles: list[str],
        conservative_articles: list[str]
) -> dict:
    j = "\n\n--- 진보 기사 ---\n" + "\n\n".join(progressive_articles)
    n = "\n\n--- 중립 기사 ---\n" + "\n\n".join(neutral_articles)
    b = "\n\n--- 보수 기사 ---\n" + "\n\n".join(conservative_articles)

    prompt = f"""
다음은 정치 성향별로 분류된 9개의 뉴스 기사 원문입니다.

{j}

{n}

{b}

위 기사를 바탕으로,
1) AI가 유의미한 비교 카테고리(예: 정책 방향, 재정 전략, 사회적 영향 등)를 **선택**하고,
2) 각 카테고리별로 진보/중립/보수 입장을 **각각 1~2문장**으로 **사실 위주로 요약**해줘.

단, 출력은 아래와 같은 구조로 깔끔하게 정리해줘:
- [카테고리 이름]
  - 진보: ...
  - 중립: ...
  - 보수: ...

※ 표 형식은 사용하지 말고 위 구조를 지켜줘.
※ 과한 해석 금지, 기사에 명시된 내용만 사용해.
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
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
    result = {}
    current_category = None
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # - [카테고리] 형식 또는 [카테고리] 또는 카테고리:
        category_match = re.match(r"^-?\s*\[?(.+?)\]?:?$", line)
        if category_match and not line.startswith("- 진보") and not line.startswith("- 중립") and not line.startswith("- 보수"):
            current_category = category_match.group(1).strip()
            result[current_category] = {}
            continue

        if current_category is None:
            continue

        if line.startswith("- 진보:"):
            result[current_category]["진보"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 중립:"):
            result[current_category]["중립"] = line.split(":", 1)[1].strip()
        elif line.startswith("- 보수:"):
            result[current_category]["보수"] = line.split(":", 1)[1].strip()

    return result



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
result_json = compare_political_orientations_gpt_json(prog, neut, cons)
import json
# 결과 출력
#print(json.dumps(result_json, ensure_ascii=False, indent=2))

# 결과 저장
with open("comparison_result.json", "w", encoding="utf-8") as f:
    json.dump(result_json, f, ensure_ascii=False, indent=2)
