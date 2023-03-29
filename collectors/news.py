import requests
import config
from bs4 import BeautifulSoup as BS
from tqdm import tqdm
import json
from pprint import pprint
import asyncio


async def save_img(url):
    try:
        img_data = requests.get(url).content
        path = url.split('/')[-2]
        with open(f'data/news_images/{path}.jpg', 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(e)


async def get_news(url):
    all_news_data = []
    r = requests.get(url + '?issue_tld=ru&utm_referrer=dzen.ru', headers=config.HEADERS_TO_NEWS)
    html = BS(r.text, "html.parser")
    html = html.find_all(class_="mg-card")
    saving_img = []
    for block in tqdm(html):
        try:
            news_data = {
                'title': block.find(class_='mg-card__title').text,
                'url': block.find(class_='mg-card__link')['href']
            }
            img = block.find(class_='mg-card__media-block')
            if 'src' in str(img):
                news_data['img'] = img.find('img')['src']
            elif 'style' in str(img) and 'url' in str(img):
                news_data['img'] = str(img['style']).split('url')[1].replace('(', '').replace(')', '')
            else:
                news_data['img'] = ''
            all_news_data.append(news_data)
            if news_data['img']:
                saving_img.append(asyncio.create_task(save_img(news_data['img'])))
        except Exception as e:
            print(e)
    await asyncio.gather(*saving_img)
    return [url, all_news_data]


async def save_all_news():
    with open('data/news_data.json', encoding='utf-8') as json_file:
        data = json.load(json_file)
    tasks = []

    for url in tqdm(config.NEWS_URLS):
        tasks.append(asyncio.create_task(get_news(url)))

    for url, dt in tqdm(await asyncio.gather(*tasks)):
        data[url] = dt
    with open('data/news_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def main():
    await save_all_news()

if __name__ == '__main__':
    asyncio.run(main())