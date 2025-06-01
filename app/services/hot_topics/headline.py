from app.utils.content_crawler import crawl_articles
from app.utils.headline_crawler import get_naver_headlines
from app.db.insertData import save_article
from app.db.findData import find_article_id_by_url
from app.db.updateData import update_headline_activate,update_headline
import asyncio


field = [100,101,102,103,104,105]
def headline_update():
    links = []
    for url in field:
        t = get_naver_headlines(section_url=f"https://news.naver.com/section/{url}")

        t = sorted(t, key=lambda x: x['best'], reverse=True)
        if url == 100:# 정치에 대해서만 3개를 다 가져옴.
            for i in t[:3]:
                a = find_article_id_by_url(i['link'])
                if a == None: # db에 없는 기사이면 크롤링 할 것임.
                    links.append(i['link']+f'?sid={url}')
                else: #있으면 headline = 0 -> 2로 바꿔줌.
                    update_headline_activate(a)
                    

        else:#정치가 아니면 1개만 가져옴.
            a = find_article_id_by_url(t[0]['link'])
            if a == None:
                links.append(t[0]['link']+f'?sid={url}')
            else:
                update_headline_activate(a)

    articles = asyncio.run(crawl_articles(links))
    

    for article in articles:
        print(article)
        save_article(article,is_headline=2)

    update_headline()

    