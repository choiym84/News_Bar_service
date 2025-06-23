# === politic_predict.py 수정본 ===

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer

# 모델 및 토크나이저 로드 함수 추가
# def load_model_and_tokenizer(save_path="app/utils/AI_Model/saved_kobigbird_kopolitic"):
#     tokenizer = AutoTokenizer.from_pretrained(save_path,local_files_only=True)
#     model = AutoModelForSequenceClassification.from_pretrained(save_path,local_files_only=True)
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(device)
#     model.to(device)

#     keywords = ["정책", "여당", "야당", "대통령", "국회", "경제", "사회", "자유", "보수", "진보", "개혁"]

#     return model, tokenizer, keywords, device

# 최종 정치성향 판단 함수 (심플 버전)
def final_predict_with_scoring_simple(text, media_orientation, model, tokenizer, keywords, device,
                                      weight_confidence=0.7,
                                      weight_keyword=0.3,
                                      threshold_strong=0.7,
                                      threshold_neutral=(0.4, 0.7)):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=3072
        ).to(device)

        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        prediction = torch.argmax(probs, dim=1).item()

        label_map = {0: "진보", 1: "보수", 2: "중립"}
        base_label = label_map[prediction]
        
        base_confidence = probs[0][prediction].item()


        # 키워드 등장 비율
        keyword_hits = sum(1 for keyword in keywords if keyword in text)
        keyword_score = keyword_hits / len(keywords)

        # 최종 점수 계산
        total_score = (base_confidence * weight_confidence) + (keyword_score * weight_keyword)

        # 최종 정치성향 결정
        if total_score >= threshold_strong:
            final_decision = base_label
            
        elif threshold_neutral[0] <= total_score < threshold_neutral[1]:
            final_decision = "중립"#base_label
        
        else:
            final_decision = "판별불가"

        result = {
            "predicted_label": base_label,
            "confidence": base_confidence,
            "match_result": (base_label == media_orientation),
            "keyword_hits": keyword_hits,
            "total_score": round(total_score, 4),
            "final_decision": final_decision
        }

        return result

## 두번째 모델이었음. gpt없이 kobigbird로만 판단하는 모델.
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

def load_model_and_tokenizer_simple(save_path="app/utils/AI_Model/save_kobigbird_model"):
    tokenizer = AutoTokenizer.from_pretrained(save_path)
    model = AutoModelForSequenceClassification.from_pretrained(save_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return model, tokenizer, device

def simple_political_match(text, media_orientation, model, tokenizer, device):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=3072
        )
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs.logits, dim=1)
        prediction = torch.argmax(probs, dim=1).item()

        label_map = {0: "진보", 1: "보수", 2: "중립"}
        predicted_label = label_map[prediction]

        return {
            "predicted_label": predicted_label,
            "confidence": probs[0][prediction].item(),
            "match_result": predicted_label == media_orientation
        }

# def simple_political_match(text, media_orientation, model, tokenizer,device):
#     model.eval()
#     with torch.no_grad():
#         inputs = tokenizer(
#             text,
#             return_tensors="pt",
#             padding="max_length",
#             truncation=True,
#             max_length=3072
#         ).to(device)

#         outputs = model(**inputs)
#         probs = torch.softmax(outputs.logits, dim=1)
#         prediction = torch.argmax(probs, dim=1).item()

#         label_map = {0: "진보", 1: "보수", 2: "중립"}
#         predicted_label = label_map[prediction]

#         return {
#             "predicted_label": predicted_label,
#             "confidence": probs[0][prediction].item(),
#             "match_result": predicted_label == media_orientation
#         }


import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import OpenAI

# GPT API 연결
client = OpenAI(api_key=os.getenv("open_ai_API_KEY"))

def gpt_rejudge_political_orientation(text: str,media: str) -> str:
    prompt = f"""
다음은 정치 뉴스 기사입니다.

{text}

이 기사의 정치적 성향을 판단해주세요. 다음 중 하나로만 답해주세요:
1. 진보
2. 보수
3. 중립

추가적으로 이 기사를 작성한 언론사의 성향은 아래와 같습니다. 내용과 너무 상반되지 않는 이상 최대한 media의 성향을 따라주세요.
{media}

조건:
- 정책 방향, 비판 대상, 주요 주장, 각 진영의 이념 등을 고려하세요.
- 무조건 한 단어로만 답해주세요 (예: 진보).
"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "너는 정치 기사 성향을 정확히 판단하는 AI야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=10,
    )

    answer = response.choices[0].message.content.strip()
    answer = answer.replace(".", "").strip()

    if "진보" in answer:
        return "진보"
    elif "보수" in answer:
        return "보수"
    elif "중립" in answer:
        return "중립"
    else:
        return "중립"


def simple_political_match_with_gpt(text, media_orientation, model, tokenizer, device):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=3072
        )
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs.logits, dim=1)
        prediction = torch.argmax(probs, dim=1).item()

        label_map = {0: "진보", 1: "보수", 2: "중립"}
        predicted_label = label_map[prediction]

        # 모든 예측에 대해 GPT로 재판단
        gpt_label = gpt_rejudge_political_orientation(text,media_orientation)
        final_label = gpt_label

        ############
        #언론사 상관없이 중립으로 나왔으면 통과
        #진보, 보수로 나오면 언론사로 나누기.
        match_result = False
        if final_label == "중립":
            match_result = True

        else:
            if (media_orientation == '진보' and final_label == '보수') or (media_orientation == '보수' and final_label == '진보'):
                match_result = False

            else: match_result = True

        return {
            "predicted_label": predicted_label,
            "media_label": media_orientation,
            "gpt_label": gpt_label,
            "final_label": final_label,
            "confidence": probs[0][prediction].item(),
            "match_result": match_result
        }

