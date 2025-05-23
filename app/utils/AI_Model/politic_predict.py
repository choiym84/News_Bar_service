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




import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def load_model_and_tokenizer_simple(save_path="app/utils/AI_Model/save_kobigbird_model"):
    tokenizer = AutoTokenizer.from_pretrained(save_path)
    model = AutoModelForSequenceClassification.from_pretrained(save_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return model, tokenizer, device

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