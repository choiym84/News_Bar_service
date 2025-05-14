
import torch
from app.db.findData import check_summary_exists,find_article_id_by_url,find_article_by_id
from app.db.insertData import summary_insert
from app.utils.AI_Model.politic_predict import load_model_and_tokenizer_simple, final_predict_with_scoring_simple,simple_political_match
from app.utils.AI_Model.summary import summarize_with_chatgpt
from app.utils.AI_Model.comparison_analysis import compare_political_orientations_gpt_json

########################################
# 0. 디바이스 및 모델, 토크나이저, 키워드 로드
########################################

# model, tokenizer, keywords, device = load_model_and_tokenizer()
model, tokenizer, device = load_model_and_tokenizer_simple()

########################################
# 4. 기사 정치성향 분석 + 매칭 + 요약
########################################


def ai_model2(articles_id):
    new_articles = []

    for id in articles_id:
        
        article = find_article_by_id(id['article_id'])
        text = article.content
        media_orientation = id['stance']

        # 기사 성향 판단.
        result = simple_political_match(
            text,
            media_orientation,
            model,
            tokenizer,
            # keywords,
            device=device
        )

        

        # 일치한 경우 요약 후 저장
        if result["match_result"]:
            
            if  check_summary_exists(id['article_id']) == False: #요약이 없거나, 기사 조차 없을 때는 요약 생성성
                summarized = summarize_with_chatgpt(text)
                # summarized = ""
                # article_id = article_insert() #기사 저장장
                summary_insert(summarized,id['article_id'],id['keyword_id']) #요약 저장

            else:
                pass 
                
            print(new_articles)
            new_articles.append(article)

        

    print("\\n[2단계] 정치성향 매칭 및 요약 완료!")
    return new_articles

########################################
# 5. 비교 분석 (각 성향별 3개 이상일 경우만)
########################################

def comparison_articles(conservative_texts,neutral_texts,progressive_texts):
    if len(progressive_texts) >= 3 and len(neutral_texts) >= 3 and len(conservative_texts) >= 3:
        comparison_result = compare_political_orientations_gpt_json(
            progressive_texts[:3],
            neutral_texts[:3],
            conservative_texts[:3]
        )
        print("\\n[3단계] 최종 비교 분석 결과:")
        print(comparison_result)
        return comparison_result
    else:
        print("\\n성향별 기사 3개 이상 확보되지 않아 비교 분석 생략됨.")

