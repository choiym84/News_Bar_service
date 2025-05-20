import logging
import asyncio
import re
from app.utils.headline_crawler import get_naver_headlines
from app.utils.naver_api import search_news_by_keyword
from app.utils.content_crawler import crawl_articles
from app.db.insertData import store_hot_topics_and_return_list, save_article
from app.utils.AI_Model.AI_main import ai_model2
from app.db.findData import find_article_id_by_url
from app.utils.AWS_img import download_image_to_local,upload_image_to_s3_from_url


# from app.utils.AI_Model.hot_topic import generate_responses
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#1차 모델
def request_first_model(titles):
    
    '''
    1차 AI 모델 임포트.
    '''
    # keywords = generate_responses(titles)
    keywords =  ["국민의힘"]#,"이재명","진보주의","대선투표","7인회","김문수"]#["김문수·국힘 지도부 발언"]#, "대법원장 탄핵 논란", "이재명 사법리스크", "김문수·국힘 지도부 발언", "김정은 장갑무력 강조", "가짜뉴스·내란세력 규정"]
    keywords = ['4년 연임제','5·18 정신 수록','국정 능력 vs 진짜 일꾼',"내란수괴",'윤 대통령 탈당','이재명 지지 선언']
    return keywords #일단 걍 넘기는거지.




#2차 모델
def request_second_model(filtered_articles):
    
    # 더미 결과 → 그냥 '찬성' / '중립' / '반대' 랜덤 or 고정값
    '''
    2차 AI 모델 임포트.
    '''


    for group in filtered_articles:
        for article in filtered_articles[group]:
            article["stance"] = "중립"
    return filtered_articles


def post_to_app_front(results):
    logger.info(f"📡 [더미] 앱 프론트로 전송됨! 결과 수: {sum(len(v) for v in results.values())}")
    print(results)  # 실제로는 requests.post 등 쓸 자리


def merge_articles(articles_link, articles):
    # 크롤링된 결과를 link 기준으로 딕셔너리화
    crawled_dict = {item["link"]: item for item in articles}

    merged = []
    for link_info in articles_link:
        link = link_info["link"]
        crawled_data = crawled_dict.get(link)

        if crawled_data:
            merged_item = {**link_info, **crawled_data}
            merged.append(merged_item)
        # else: 크롤링 실패한 경우는 추가하지 않음!
    return merged


#불용어 txt 호출.
def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        stopwords = [line.strip() for line in f if line.strip()]
    return stopwords


def clean_text(text):
    """
    텍스트에서 특수문자, 기호 제거
    (한글, 영어, 숫자, 공백만 남기기)
    """
    # 한글, 영어, 숫자, 공백 외 모두 제거
    return re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)

#키워드에 불용어 처리.
def preprocess_keywords(keywords, stopwords):
    """
    모델 1 결과 키워드 리스트 → 불용어 제거된 키워드 리스트
    """
    processed = []
    for keyword in keywords:
        cleaned_keyword = clean_text(keyword)  
        tokens = cleaned_keyword.strip().split()  # 띄어쓰기로 나눠
        filtered_tokens = [token for token in tokens if token not in stopwords]
        processed_keyword = " ".join(filtered_tokens)  # 다시 합치기
        if processed_keyword:  # 비어있지 않은 경우만 추가
            processed.append(processed_keyword)
    return processed


#언론사에 의한 정치성향 필터링.
def label_media_bias(data):
    conservative = {"조선일보", "중앙일보", "동아일보", "문화일보", "국민일보", "tv조선", "채널A"}
    progressive = {"한겨레", "경향신문", "미디어오늘", "오마이뉴스", "MBC", "JTBC", "프레시안", "민중의소리"}
    centrist = {"서울신문", "한국일보", "내일신문", "뉴시스", "연합뉴스", "파이낸셜뉴스"}


    new_data = []
    delete_article = 0
    con,cen,pro = 0,0,0

    for article in data:

        if article['publisher'] in conservative:
            article['stance'] = '보수'
            new_data.append(article)
            con += 1
            
        elif article['publisher'] in progressive:
            article['stance'] = '진보'
            new_data.append(article)
            pro += 1
            
        elif article['publisher'] in centrist:
            article['stance'] = '중립'
            new_data.append(article)
            cen += 1
            
        else:
            delete_article += 1

    return new_data,delete_article,con,cen,pro



def start_pipeline():
    logger.info("[Hot Topic Pipeline] 수집 시작 ✅")
    asdf = 0
    # 1. 헤드라인 크롤링
    headlines = get_naver_headlines()
    s = []
    for k in headlines:
        s.append(k["title"])
    logger.info(f"1번 데이터 확인 : {s}")
    print("#############################################")
    # 2. 모델 1 → 키워드 추출
    keywords = request_first_model(s)
    logger.info(f"2번 데이터 확인 : {keywords}")
    keywords = preprocess_keywords(keywords,load_stopwords("app//Stopwords.txt"))
    keywords = store_hot_topics_and_return_list(keywords)

    
    print("#############################################")
    # 3. 키워드 기반 뉴스 검색
    for keyword in keywords:
        articles_link = search_news_by_keyword(keyword)

        logger.info(f"{keyword}의 기사 갯수 : {len(articles_link)}")
        #링크들만 뽑아놓음
        links = [item["link"] for item in articles_link]

        # 4. 뉴스 검색 + 본문 크롤링 (비동기)
        articles = asyncio.run(crawl_articles(links))
        data = merge_articles(articles,articles_link) # 데이터 형태{}
        for i in data:
            i['keyword'] = i['keyword']['id']

        # 5. 언론사 필터링

        '''
        이부분은 좀더 고민이 필요함. 현재는 성향별로 각각 3개, 총 9개의 기사만 뽑히게 됨.
        그래서 혹시 데이터가 부족하진 않을까? 라는 걱정이 듦. 이 부분은 좀 체크가 필요

        -> 먼저 성향일치 불문하고 필터링을 통과한 기사는 모두 db에 저장한다.
        '''
        data,idx,con,cen,pro = label_media_bias(data)

        logger.info(f"언론사 라벨링에서 총 {idx}개의 기사가 제거되었습니다.")
        logger.info(f"이번 키워드의 성향별 기사 갯수 : 보수 {con}개, 중도 {cen}개, 진보 {pro}개") #
        

        new_data=[]
        # 6. 기사 저장
        for i in data:
            a = find_article_id_by_url(i['link'])
            if a: #있으면
                pass
            else: #기존에 기사가 없으면
                a = save_article(i)

            new_data.append({'article_id':a,'keyword_id':i['keyword'],'stance':i['stance']})

        logger.info("기사 저장 완료")


        print(len(new_data))
        # 7. 기사 요약
        
        data = ai_model2(new_data) #성향에 따라 3개 3개 3개의 기사만 넘어올거임.
        # print(len(data)) #일치 하는 것만 넘어옴. 아래 주석이 데이터 형태.

        
        '''
        {'title', 'content', 'publisher', 'reporter', 'link', 'keyword': {'keyword': '김문수국힘 지도부 발언', 'id': 105}, 'pub_date', 'stance'}
        '''

        # 기사 저장하고 id 받아옴.
        # data = store_filtered_articles_and_return_info(data, keyword['id'])
        # analyzed_results = request_second_model(filtered_articles)

    
    print("[Hot Topic Pipeline] 수집 완료 ✅")
    logger.info("[Hot Topic Pipeline] 수집 완료 ✅")
