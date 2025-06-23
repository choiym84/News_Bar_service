from app.db.findData import check_summary_exists,find_article_id_by_url,find_article_by_id
from app.db.insertData import summary_insert, bridge_conn,save_analyze
from app.utils.AI_Model.politic_predict import load_model_and_tokenizer_simple, final_predict_with_scoring_simple,simple_political_match,simple_political_match_with_gpt
from app.utils.AI_Model.summary import summarize_with_chatgpt
from app.utils.AI_Model.comparison_analysis import compare_political_orientations_gpt_json
from app.utils.findFake.all_pass_news_direct import evaluate_article

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
    con = []
    cen = []
    pro = []

    for id in articles_id:
        
        article,_ = find_article_by_id(id['article_id'])
        text = article.content
        media_orientation = id['stance']
        link = article.url

        # 기사 성향 판단.
        result = simple_political_match_with_gpt(
            text,
            media_orientation,
            model,
            tokenizer,
            # keywords,
            device=device
        )

        result['link'] = link
        ######위험도 분석 

        # fake_score = evaluate_article(article.title, text, article.publish_date, article.publisher)
        # print(fake_score)
        # if fake_score >= 0.6:
        #     print("###위험도 높음###")
        #     continue
        #####
        print(result)
        # 일치한 경우 요약 후 저장
        if result["match_result"]:
            
            if len(cen) == 3 and len(pro) == 3 and len(con) == 3: #모든 것이 꽉차면 멈춤
                break

            elif result["final_label"] == '중립' and len(cen) < 3: #중립 3개 이하
                cen.append(id)
                new_articles.append(id)
                

            elif result["final_label"] == '보수' and len(con) < 3: #보수 3개 이하
                con.append(id)
                new_articles.append(id)
                

            elif result["final_label"] == '진보' and len(pro) < 3: #진보 3개 이하
                pro.append(id)
                new_articles.append(id)
                

            else:
                
                continue

            
            if check_summary_exists(id['article_id']) == None: #요약이 없거나, 기사 조차 없을 때는 요약 생성
                summarized = summarize_with_chatgpt(text)
                #기사 저장
                summary_insert(summarized,id['article_id'],id['keyword_id']) #요약 저장

            else:
                pass


            bridge_conn(id['article_id'],id['keyword_id'],result["final_label"])
            
    
        ##넘기기 전에 성향별 요약 한번 하고 넘어가도 괜찮을 것 같다.
        ##con,cen,pro 어떻게 해야 할까?

    print("\\n[2단계] 정치성향 매칭 및 요약 완료!")
    return new_articles

########################################
# 5. 비교 분석 (각 성향별 3개 이상일 경우만)
########################################

def ai_model3(ids,keyword):
    if True:#len(progressive_texts) >= 3 and len(neutral_texts) >= 3 and len(conservative_texts) >= 3:
        
        progressive_texts = []
        neutral_texts = []
        conservative_texts = []

        for id in ids:
            data,_ = find_article_by_id(id['article_id'])
            text = data.content
            if id['stance'] == '보수':
                conservative_texts.append(text)
            elif id['stance'] == '중립':
                neutral_texts.append(text)
            else:
                conservative_texts.append(text)

            
        

        comparison_result = compare_political_orientations_gpt_json(
            progressive_texts[:3],
            neutral_texts[:3],
            conservative_texts[:3],
            keyword['keyword']
            
        )
        print("\\n[3단계] 최종 비교 분석 결과:")
        print(comparison_result)
        save_analyze(comparison_result,keyword['id'])
        return comparison_result
    else:
        print("\\n성향별 기사 3개 이상 확보되지 않아 비교 분석 생략됨.")

