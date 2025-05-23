import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
import re

# ✅ 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("open_ai_API_KEY"))


# ✅ Chroma 벡터스토어 로드 (cosine 공간)
def load_vectorstore(persist_path="./gov_combined_db"):
    embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
    return Chroma(
        persist_directory=persist_path,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )


# ✅ 프롬프트 템플릿 구성
def build_prompt(context, title, question):
    prompt_template = """
    
다음은 정부기관의 문서 일부입니다. 기사 제목과 내용을 중심으로 판단하되, 문서 내용이 판단에 도움이 될 경우 참고해 주세요. 관련이 없다면 무시해도 됩니다.  

[참고 문서]
{context}

이제 기사 제목과 기사 내용을 알려드리겠습니다.

[기사 제목]
{title}

[기사 내용]
{question}

아래 4가지 기준을 바탕으로 예시 기사에 대해 판단해주세요. 외부 출처나 참고문서뿐 아니라, 일반적인 상식이나 당신의 지식 범위 내에서 먼저 검증해주세요. [참고문서]는 '보조적'으로 활용됩니다.:

1.	사실 확인 가능 여부:
기사에 등장한 정보가 외부 출처, 참고문서, 또는 일반적인 지식으로 교차 검증 가능한가요?
2.	공식 출처 언급 여부:
기사에서 정부 기관, 공공 인물, 공식 문서 등 신뢰할 수 있는 출처를 명확히 언급했는지 판단해 주세요.
3.	과장된 표현 여부:
선동적이거나 감정을 자극하는 표현, 현실에 비해 과도하게 부풀려진 수치나 피해 주장, 또는 사실 여부가 불분명한 극단적 표현이 사용되었는지 확인해 주세요.
4.	논리적 오류 여부:
기사 내 주장들 사이에 논리적 비약, 원인과 결과 간 모순, 혹은 결론을 뒷받침하지 못하는 근거 등이 있는지 확인해 주세요.

[출력 형식]
- 각 항목에 대해 “있다/없다/그렇다/아니다” 등으로 먼저 판단해서 적어주고, 한두 문장의 근거를 적어주세요.
- 각 항목은 반드시 아래 형식을 지켜주세요. 모든 항목에 대해서 **응답은 콜론(:) 다음에 한 단어 판단, 그리고 줄바꿈 후 한두 문장의 근거**로 구성해주세요.
- 그리고 추가적으로 예시 기사를 기반으로 네이버 뉴스 검색에 사용할 만한 핵심 키워드 5개를 뽑아주세요.

1. 사실 확인 가능 여부 :
2. 공식 출처 언급 여부 :
3. 과장된 표현 여부 :
4. 논리적 오류 여부 :
[검색 키워드]
- 키워드1
- 키워드2
- 키워드3
- 키워드4
- 키워드5
"""
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "title", "question"]
    )
    return prompt.format(context=context, title=title, question=question)


# ✅ GPT 호출
def generate_answer_with_gpt(prompt, model="gpt-4o"):
    messages = [
        {"role": "system", "content": "너는 정부 문서를 보조적으로 이용해서 기사에 대한 판단을 도와주는 AI야. 기준에 따라 정확히 응답해줘."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    result = response.choices[0].message.content.strip()

    # ✅ "2. 공식 출처 언급 여부 :" 값을 추출
    공식출처_있음 = bool(re.search(r"2\. 공식 출처 언급 여부\s*:\s*(있다|그렇다)", result))
    return result, 공식출처_있음


# ✅ 문서 검색 → 프롬프트 구성 → 응답 생성 (threshold 필터링 추가)
def answer_with_gpt(vectorstore, title, content, k, threshold):
    # 1) 코사인 유사도 점수와 함께 상위 k개 문서 가져오기
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(content, k=k)
    # [(Document, cosine_similarity), ...]

    # 2) threshold 필터링
    filtered = [(doc, sim) for doc, sim in docs_and_scores if sim >= threshold]

    # 3) 필터링 결과 출력
    if filtered:
        for i, (doc, sim) in enumerate(filtered, 1):
            snippet = doc.page_content[:200].replace("\n", " ")
        docs = [doc for doc, _ in filtered]
        context = "\n\n".join([d.page_content[:800] for d in docs])
    else:
        docs = []
        context = ""  # 컨텍스트 없이 프롬프트 구성


    # 4) GPT 프롬프트 생성 및 호출
    prompt = build_prompt(context=context, title=title, question=content)
    result_text, official = generate_answer_with_gpt(prompt)

    # 5) 출력
    if official and docs:
        date = docs[0].metadata.get("date", "날짜 정보 없음")

    return result_text


# ✅ 메인 실행
if __name__ == "__main__":
    title = "\"장시간 노동, 이제 그만\"…주4.5일제가 온다"
    article = """
뉴스를 깊이 있게 들여다보는 '앵커리포트' 순서입니다.
2023년 기준 국내 노동자의 연간 노동시간은 1,872시간으로, OECD 회원국 가운데 여섯 번째로 많았습니다.
OECD 평균보다 130시간이 더 길고, 노동시간이 가장 짧은 독일보다는 무려 529시간, 매달 44시간 더 일하고 있습니다.
이처럼 살인적인 노동시간은 노동자를 하루하루 죽음으로 몰아넣고 있습니다.
세계보건기구에 따르면 주 55시간 이상 일할 경우 허혈성 심장질환 위험은 17%, 뇌졸중은 35% 증가합니다.
우리나라에서 매년 500명이 과로로 사망한다는 통계도 있습니다.
[김용복/한국노총 대전본부 의장 : "오래 일한다고 생산성이 높아지지 않습니다. 근로시간을 줄이면 삶의 질이 개선되고, 일·가정 양립이 가능해져 저출산 문제 해결에도 도움이 됩니다."]
워라벨에 대한 요구가 커지면서 이번 대선에서도 주요 의제로 떠올랐습니다.
민주당 이재명 대선 후보는 주4.5일제를 거쳐 주4일제 도입을 추진하겠다고 밝혔고, 국민의힘 김문수 후보도 주 4.5일제 도입 의지를 보이고 있습니다.
이재명 후보는 노동시간 자체의 단축을, 김문수 후보는 유연근무 형태를 확대하는 방식에 방점을 두고 있지만, 두 후보 모두 노동시간 구조 변화가 필요하다는 데는 공감하고 있습니다.
하지만 제도 도입까지는 넘어야 할 과제가 적지 않습니다.
가장 큰 우려는 노동시간이 줄어드는 만큼 기존 임금이 유지될 수 있느냐입니다.
또 공공기관이나 대기업에서는 도입이 가능할 수 있지만, 서비스업이나 중소기업에서는 대체 인력 확보와 인건비 부담으로 적용이 쉽지 않다는 지적도 있습니다.
[김종진/일하는시민연구소 소장 : "전 세계적으로 법정 노동시간을 단축하는 노동시간 단축 같은 경우에는, 노사정이 합의를 통해서 해야만 파고도 적고 사회적 충격을, 여파를 줄일 수 있습니다."]
그렇다면 해법은 무엇일까요?
전문가들은 주 52시간제 도입 당시처럼 단계적 접근을 제안합니다.
업종과 직무 특성에 따라 시범 도입하고 효과와 문제점을 점검하며 점차 확대하는 방식입니다.
정부의 정책적 뒷받침도 필수적입니다.
[윤동열/건국대 경영학과 교수 : "중소기업의 인건비 부담을 좀 완화하기 위한 세제 혜택이라든지, 고용 지원금이라든지, 사회보험료 감면 등의 정책을 수행할 수 있을 거라고 보고요."]
우리나라는 과학기술의 발달과 산업 구조 변화에 맞춰 주5일제, 주 52시간제 등 노동시간 개혁을 꾸준히 추진해 왔습니다.
그다음 단계인 주4.5일제는 언제 현실화될 지 알 수 없지만, 한 가지 분명한 것은 인공지능 시대를 맞아 일자리 패러다임이 변화하고 있는 만큼 4.5일제 논의와 검토의 필요성은 충분하다는 겁니다.
지금까지 앵커리포트였습니다.
"""
    vectorstore = load_vectorstore()
    result = answer_with_gpt(vectorstore, title, article, k=3, threshold=0.6)
    print("\n최종 응답:\n", result)