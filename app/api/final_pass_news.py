import re
import os
import tempfile
import shutil
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, Request
from app.db.findData import hot_topic_pipeline,find_activate_hottopic,find_hottopic_detail_by_id
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.schemas.article_schema import ArticleRequest
from app.utils.findFake.naver_ocr_2 import ocr_and_extract_text
from app.utils.findFake.db_find_info_2 import (
    # get_article_url_by_title_fuzzy,
    crawl_naver_news_article,
    get_article_by_press_and_lines_news_details,
    crawl_naver_news_article_url
)

from app.utils.findFake.final_pass_utils import evaluate_article, parse_gpt_output_to_items, summarize_article

load_dotenv()


#고칠 부분 : app = Flask(__name__), @app.route('/api/v1/analysis/factcheck/image', methods=['POST']),  return jsonify({
# ✅ Flask 서버 추가

router = APIRouter()

@router.post('/api/v1/analysis/factcheck/image')
async def analyze_image_factcheck(image: UploadFile = File(...)):
    try:
        # 1) Flutter에서 전송된 이미지 파일 받기
        # if 'image' not in request.files:
        #     return jsonify({'status': 'error', 'message': 'image 파일이 없습니다.'}), 400
        # img_file = request.files['image']

       

        if not image:
            raise HTTPException(status_code=400, detail="image 파일이 없습니다.")

        # 2) 임시 파일로 저장
        # tmp = tempfile.NamedTemporaryFile(delete=False,
        #                                   suffix=os.path.splitext(img_file.filename)[1])
        # img_file.save(tmp.name)
        # tmp.close()
        
        suffix = os.path.splitext(image.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(image.file, tmp)
            tmp_path = tmp.name
        
        
        

        # 3) OCR 수행
        # full_text, media_outlets = ocr_and_extract_text(tmp.name)
        # os.unlink(tmp.name)
        # if not media_outlets:
        #     return jsonify({'status': 'error', 'message': '언론사 검색 결과 없음'}), 200
        
        full_text, media_outlets = ocr_and_extract_text(tmp_path)
        
        os.unlink(tmp_path)
        if not media_outlets:
            return JSONResponse(
                content={"status": "error", "message": "언론사 검색 결과 없음"}, status_code=200)
        
        

       
        # 4) DB 검색 및 크롤링
        # press = media_outlets[0]
        # db_match = get_article_by_press_and_lines_news_details(press, full_text) #url,title,date

        # if not db_match:
        #     return jsonify({'status': 'error', 'message': '유사한 기사 찾기 실패'}), 200
        # url, _ = db_match
        # article_info = crawl_naver_news_article(url)
        # if not article_info:
        #     return jsonify({'status': 'error', 'message': '기사 크롤링 실패'}), 200

        # title   = article_info['title']
        # content = article_info['content']
        # media   = article_info['press']

        press = media_outlets[0]
        db_match = get_article_by_press_and_lines_news_details(press, full_text)
        if not db_match:
            return JSONResponse(
                content={"status": "error", "message": "유사한 기사 찾기 실패"}, status_code=200)
        
    

        url, t, date = db_match
        print(url,t,date)
        article_info = crawl_naver_news_article(url)
        if not article_info:
            return JSONResponse(
                content={"status": "error", "message": "기사 크롤링 실패"}, status_code=200)
        


        title = article_info["title"]
        content = article_info["content"]
        media = article_info["press"]


        # 5) 날짜 조회
        # result_url = get_article_url_by_title_fuzzy(title)
        # 이 부분은 필요가 없음.

        print("1")

        # 6) 평가 실행
        # model_path = "/Users/hansangjun/Desktop/Capstone_Backend/news_naver_API/4-6/kobigbird_finetuned_epoch_6"
        eval_result = evaluate_article(title, content, date, media)

        print("2")

        # 7) GPT 진단 결과 파싱 → factCheckResults
        #    [검색 키워드] 이하 제거
        raw = eval_result["gpt_output"]
        gpt_output = raw.split("[검색 키워드]")[0].strip() if "[검색 키워드]" in raw else raw
        fact_items = parse_gpt_output_to_items(gpt_output)

        print("3")

        # 8) 언론사 신뢰도·최초 확산·반복 패턴을 별도 factCheckResults 항목으로 추가
        fact_items.extend([
            {
                "item":       "언론사 신뢰도",
                "result":     "",
                "hasWarning": None,
                "reason":     str(eval_result["risk_penalty"])
            },
            {
                "item":       "최초 확산 지점",
                "result":     "",
                "hasWarning": None,
                "reason":     eval_result["earliest_diffusion"]
            },
            {
                "item":       "반복 확산 패턴",
                "result":     "",
                "hasWarning": None,
                "reason":     eval_result["repetition_pattern"]
            },
        ])

        # 9) 최종 JSON 구조로 반환
        # return jsonify({
        #     "status": "success",
        #     "data": {
        #         "type":             "factcheck",
        #         "title":            title,
        #         "factCheckResults": fact_items,
        #         "conclusion":       str(eval_result["final_risk"])
        #     }
        # }), 200
    
        return {
            "status": "success",
            "data": {
                "type": "factcheck",
                "title": title,
                "factCheckResults": fact_items,
                "conclusion": str(eval_result["final_risk"])
            }
        }

    # except Exception as e:
    #     print(f"Server error: {e}")
    #     return jsonify({'status': 'error', 'message': '서버 오류'}), 500

    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)


@router.post('/api/v1/analysis/summary/image')
async def analyze_image_summary(image: UploadFile = File(...)):
    try:
        # 1) multipart/form-data 로 받은 이미지
        # if 'image' not in request.files:
        #     return jsonify({'status': 'error', 'message': 'image 파일이 없습니다.'}), 400
        # img_file = request.files['image']
        if not image:
            raise HTTPException(status_code=400, detail="image 파일이 없습니다.")

        # 2) 임시 저장
        # tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img_file.filename)[1])
        # img_file.save(tmp.name)
        # tmp.close()

        suffix = os.path.splitext(image.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(image.file, tmp)
            tmp_path = tmp.name

        # 3) OCR
        # full_text, media_outlets = ocr_and_extract_text(tmp.name)
        # os.unlink(tmp.name)
        # if not media_outlets:
        #     return jsonify({'status': 'error', 'message': '언론사 검색 결과 없음'}), 200

        full_text, media_outlets = ocr_and_extract_text(tmp_path)
        
        os.unlink(tmp_path)
        if not media_outlets:
            return JSONResponse(
                content={"status": "error", "message": "언론사 검색 결과 없음"}, status_code=200)




        # 4) DB 검색 & 크롤링
        # press = media_outlets[0]
        # db_match = get_article_by_press_and_lines_news_details(press, full_text)
        # if not db_match:
        #     return jsonify({'status': 'error', 'message': '유사한 기사 찾기 실패'}), 200
        # url, _ = db_match
        # article_info = crawl_naver_news_article(url)
        # if not article_info:
        #     return jsonify({'status': 'error', 'message': '기사 크롤링 실패'}), 200

        # title   = article_info['title']
        # content = article_info['content']
        press = media_outlets[0]
        db_match = get_article_by_press_and_lines_news_details(press, full_text)
        if not db_match:
            return JSONResponse(
                content={"status": "error", "message": "유사한 기사 찾기 실패"}, status_code=200)

        url, t, date = db_match
        article_info = crawl_naver_news_article(url)
        if not article_info:
            return JSONResponse(
                content={"status": "error", "message": "기사 크롤링 실패"}, status_code=200)
        


        title = article_info["title"]
        content = article_info["content"]



        # 5) 요약 실행
        summary_text = summarize_article(title, content)

        # 6) 결과 반환
        return JSONResponse(
        status_code=200,
        content={
        'status': 'success',
        'data': {
            'type': 'summary',
            'title': title,
            'content': summary_text
        }
        }
    )

    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)
    

@router.post('/api/v1/analysis/summary')

async def analyze_article_by_url_summary(request:ArticleRequest):
    try:
        url = request.url

        if not url:
            return JSONResponse(
                status_code=400,
                content={'result': '❌ URL이 전달되지 않았습니다.'}
            )

        article_info = crawl_naver_news_article_url(url)
        if not article_info:
            return JSONResponse(
                status_code=200,
                content={'result': '❌ 기사 크롤링 실패'}
            )

        title = article_info['title']
        content = article_info['content']
        summary_text = summarize_article(title, content)

        return JSONResponse(
            status_code=200,
            content={
                'status': 'success',
                'data': {
                    'type': 'summary',
                    'title': title,
                    'content': summary_text
                }
            }
        )

        # # 1) JSON 요청으로부터 URL 받기
        # data = request.get_json()
        # url = data.get("url")
        # if not url:
        #     return jsonify({'result': '❌ URL이 전달되지 않았습니다.'}), 400

        # # 2) 기사 본문 크롤링
        # article_info = crawl_naver_news_article_url(url)
        # if not article_info:
        #     return jsonify({'result': '❌ 기사 크롤링 실패'}), 200

        # content = article_info['content']
        # media   = article_info['press']
        # title = article_info['title']
        # # 3) 요약 실행
        # summary_text = summarize_article(title, content)

        # # 4) 결과 반환
        # return jsonify({
        #     'status': 'success',
        #     'data': {
        #         'type': 'summary',
        #         'title': title,
        #         'content': summary_text
        #     }
        # }), 200

    except Exception as e:
        print(f"Server error: {e}")
        return JSONResponse(
            content={"status": "error", "message": "서버 오류"}, status_code=500)

@router.post('/api/v1/analysis/factcheck')
async def analyze_article_by_url_factcheck(request):
    try:
        data = request.get_json()
        url = data.get("url")
        if not url:
            return jsonify({'status': 'error', 'message': 'URL이 전달되지 않았습니다.'}), 400
        # 1) Crawl article content
        article_info = crawl_naver_news_article_url(url)
        if not article_info:
            return jsonify({'status': 'error', 'message': '기사 크롤링 실패'}), 200
        content = article_info['content']
        media   = article_info['press']
        title = article_info['title']
        date = article_info['date']
        # 2) Evaluate
        # model_path = "/Users/hansangjun/Desktop/Capstone_Backend/news_naver_API/4-6/kobigbird_finetuned_epoch_6"
        eval_result = evaluate_article(title, content,  date, media)

        # 3) Parse GPT output
        raw = eval_result["gpt_output"]
        gpt_text = raw.split("[검색 키워드]")[0].strip()
        fact_items = parse_gpt_output_to_items(gpt_text)

        # 4) Append penalty and pattern items
        fact_items.extend([
            {
                "item": "언론사 신뢰도", 
                "result": "",
                "hasWarning": None, 
                "reason": str(eval_result["risk_penalty"])
            },
            {
                "item": "최초 확산 지점", 
                "result": "", 
                "hasWarning": None, 
                "reason": eval_result["earliest_diffusion"]
            },
            {
                "item": "반복 확산 패턴", 
                "result": "", 
                "hasWarning": None, 
                "reason": eval_result["repetition_pattern"]
            }
        ])
        print(fact_items)
        return jsonify({
            "status": "success",
            "data": {
                "type": "factcheck",
                "title": title,
                "factCheckResults": fact_items,
                "conclusion": str(eval_result["final_risk"])
            }
        }), 200

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'status': 'error', 'message': '서버 오류'}), 500
    

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=8000, debug=True)