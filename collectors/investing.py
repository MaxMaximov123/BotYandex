import requests
import json
from pprint import pprint
import logging
from threading import Thread
from tqdm import tqdm
from scripts import config
import os
import asyncio

logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOGFORMAT,
)
all_stoks = {}
path_ = ''


# ПАРСЕР ДЛЯ СБОРА ДАННЫХ АКЦИЙ
def get_stok(country):
    global all_stoks

    # JSON ДЛЯ ПЛУЧЕНИЯ ДАННЫХ
    json_ = {
        "columns": [
            "name", "description", "logoid", "update_mode", "type", "typespecs", "close", "currency",
            "pricescale", "minmov", "fractional", "minmove2", "change", "change_abs", "Recommend.All",
            "volume", "Value.Traded", "market_cap_basic", "fundamental_currency_code",
            "price_earnings_ttm", "earnings_per_share_basic_ttm", "number_of_employees", "sector",
            "market"],
        "filter": [],
        "filterOR": [],
        "ignore_unknown_fields": False,
        "options": {"active_symbols_only": True, "lang": "ru"},
        "price_conversion": {},
        "range": [0, 9999999],
        "sort": {"sortBy": "name", "sortOrder": "asc"},
        "symbols": {"query": {"types": []}, "tickers": []},
        # "typespecs": ['preferred', 'common'],
        "markets": []}

    # ПОЛУЧЕНИЕ ДАННЫХ
    try:
        r = requests.post(f"https://scanner.tradingview.com/{country}/scan", json=json_)
        cont = json.loads(r.text)['data']
        for i in cont:
            stonks_ = i['d']
            title = stonks_[0] + ' | ' + stonks_[1] + f' ({country})'
            if len(str(stonks_[15])) < 4:
                turnover = str(stonks_[15])
            elif 7 > len(str(stonks_[15])) >= 4:
                turnover = str(round(stonks_[15] / 1000, 3)) + 'K'
            elif 10 > len(str(stonks_[15])) >= 7:
                turnover = str(round(stonks_[15] / 1000000, 3)) + 'M'
            else:
                turnover = str(round(stonks_[15] / 1000000000, 3)) + 'B'
            all_stoks[title] = {
                'name': str(stonks_[1]),
                'logoId': str(stonks_[0]),
                'daily_dinamic_proc': stonks_[-12],
                'daily_dinamic_price': stonks_[-11],
                'price': stonks_[6],
                'turnover': turnover,
                'field': str(stonks_[-2]),
                'country': str(stonks_[-1]),
                'cur': str(stonks_[7]),
                'stock_market': i['s'].split(':')[0],
                'img': str(stonks_[2])
            }

    except Exception as e:
        logging.warning(f'{country} | {e}')


def save_all_stocks():
    tasks = []
    logging.info('start getting stocks')
    for i in config.COUNTRIES:
        tasks.append(Thread(target=get_stok, args=(i,)))
        tasks[-1].start()
    [i.join() for i in tasks]
    logging.info('getting stocks complete')
    with open(f'{path_}data/stocks_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_stoks, f, ensure_ascii=False, indent=4)
    return all_stoks



# ЗАГОЛОВОК ЗАПРОСА
head = {
    'cookie': '_ga=GA1.2.52789296.1648979760; cookiePrivacyPreferenceBannerProduction=notApplicable;'
              ' cookiesSettings={"analytics":true,"advertising":true}; g_state={"i_p":1666534732393,'
              '"i_l":4}; _gid=GA1.2.329261428.1664702353; _sp_ses.cf1a=*; _gat_gtag_UA_24278967_1=1;'
              ' _sp_id.cf1a=20b4efa2-04fb-4650-8cef-f25885fcba00.1648979760.21.1664717312.1664710231.'
              'c311379f-2752-4ec1-b5c3-c409fa3bbe91',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/'
                  '537.36 (KHTML, like Gecko) Chrome/104.0.5112.114 Safari/537.36'}


# ПОЛУЧЕНИЕ СПИСКА НОВОСТЕЙ
def get_news(stock_market, logoId, img, save_img=False):
    r = requests.get(f'https://news-headlines.tradingview.com/headlines/'
                     f'?category=stock&lang=ru&symbol={stock_market}%3A{logoId}', headers=head)
    if save_img and img and not os.path.exists(f'icons/{img}.svg'):
        img_data = requests.get(f'https://s3-symbol-logo.tradingview.com/{img}--big.svg').content
        with open(f'{path_}icons/{img}.svg', 'wb') as handler:
            handler.write(img_data)
    cont = json.loads(r.text)
    news = []
    for i in cont:
        if 'tag' in i['id']:
            url = i['id'][4:]
        else:
            url = i['id']
        url = 'https://ru.tradingview.com/news/' + url
        news.append({
            'title': i['title'],
            'url': url,
            'img': f'https://s3-symbol-logo.tradingview.com/{img}--big.svg'
        })
    return news


if __name__ == '__main__':
    path_ = '../'
    save_all_stocks()
    pprint(len(all_stoks))
