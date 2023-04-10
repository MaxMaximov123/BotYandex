import requests
import json
from pprint import pprint


# ПАРСЕР ДЛЯ СБОРА ДАННЫХ АКЦИЙ
def stoks(country):
    # СТРУКТУРА ДАННЫХ
    all_stoks = {
        'name': [],
        'logoId': [],
        'daydinamic_proc': [],
        'daydinamic_price': [],
        'turnover': [],
        'price': [],
        'cur': [],
        'field': [],
        'country': [],
        'stock market': [],
        'img': []}

    # JSON ДЛЯ ПЛУЧЕНИЯ ДАННЫХ
    json_ = {"columns": ["name", "description", "logoid", "update_mode", "type", "typespecs", "close", "currency",
                         "pricescale", "minmov", "fractional", "minmove2", "change", "change_abs", "Recommend.All",
                         "volume", "Value.Traded", "market_cap_basic", "fundamental_currency_code",
                         "price_earnings_ttm", "earnings_per_share_basic_ttm", "number_of_employees", "sector",
                         "market"],
             "filter": [{"left": "typespecs", "operation": "has", "right": "common"},
                        {"left": "typespecs", "operation": "has_none_of", "right": "foreign-issuer"},
                        {"left": "type", "operation": "equal", "right": "stock"}],
             "filterOR": [],
             "ignore_unknown_fields": False,
             "options": {"active_symbols_only": True, "lang": "ru"},
             "price_conversion": {},
             "range": [0, 9999999],
             "sort": {"sortBy": "name", "sortOrder": "asc"},
             "symbols": {"query": {"types": []}, "tickers": []},
             "markets": [country]}

    # ПОЛУЧЕНИЕ ДАННЫХ
    try:
        r = requests.post(f"https://scanner.tradingview.com/{country}/scan", json=json_)
        cont = json.loads(r.text)['data']
        pprint(cont)
        # for i in cont:
        #     stonks_ = i['d']
        #     if len(str(stonks_[15])) < 4:
        #         turnover = str(stonks_[15])
        #     elif 7 > len(str(stonks_[15])) >= 4:
        #         turnover = str(round(stonks_[15] / 1000, 3)) + 'K'
        #     elif 10 > len(str(stonks_[15])) >= 7:
        #         turnover = str(round(stonks_[15] / 1000000, 3)) + 'M'
        #     else:
        #         turnover = str(round(stonks_[15] / 1000000000, 3)) + 'B'
        #     all_stoks['name'].append(str(stonks_[1]))
        #     all_stoks['logoId'].append(str(stonks_[0]))
        #     all_stoks['daydinamic_proc'].append(stonks_[-12])
        #     all_stoks['daydinamic_price'].append(stonks_[-11])
        #     all_stoks['price'].append(stonks_[6])
        #     all_stoks['turnover'].append(turnover)
        #     all_stoks['field'].append(str(stonks_[-2]))
        #     all_stoks['country'].append(str(stonks_[-1]))
        #     all_stoks['cur'].append(str(stonks_[7]))
        #     all_stoks['stock market'].append(i['s'].split(':')[0])
        #     all_stoks['img'].append(str(stonks_[2]))

    except Exception as e:
        print(999, country, e)
    return all_stoks


if __name__ == '__main__':
    (pprint([stoks(i) for i in ['america', 'russia']]))
