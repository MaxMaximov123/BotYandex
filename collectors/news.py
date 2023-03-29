import requests
import config
from bs4 import BeautifulSoup as BS
from tqdm import tqdm
import json
from pprint import pprint
import asyncio


async def get_news(url):
    try:
        r = requests.get(url + '?issue_tld=ru&utm_referrer=dzen.ru', headers=config.HEADERS_TO_NEWS)
        html = BS(r.text, "html.parser")
        if url == "https://yandex.ru/news":
            html = html.find(class_="mg-grid__row mg-grid__row_gap_8 news-top-flexible-stories news-app__top")
        news = [i.text for i in html.find_all(class_="mg-card__title")]
        img_html = html.find_all(class_='mg-card__media-block')
        img = []
        for i in img_html:
            if i.find('img'):
                img.append(i.find('img')['src'])
            else:
                img.append(str(i['style']).split('url')[1].replace('(', '').replace(')', ''))
        detailed_urls = [i['href'] for i in html.find_all(class_="mg-card__link")]
        return url, news, detailed_urls, img
    except Exception as error:
        print(error)
        return [], ""


async def save_html():
    with open('../data/news_data.json') as json_file:
        data = json.load(json_file)
    tasks = []
    for url in tqdm(config.NEWS_URLS):
        tasks.append(asyncio.create_task(get_news(url)))

    for inp_d in await asyncio.gather(*tasks):
        try:
            if all([inp_d[0], inp_d[1], inp_d[2], inp_d[3]]):
                data[inp_d[0]] = (inp_d[1], inp_d[2], inp_d[3])
        except Exception as error:
            print(error)
    pprint(data)


async def main():
    await save_html()

if __name__ == '__main__':
    asyncio.run(main())