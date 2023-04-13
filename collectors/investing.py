import requests
import json
from pprint import pprint
import logging
from threading import Thread
from tqdm import tqdm
from scripts import config
import asyncio

LOG_LEVEL = logging.INFO
LOGFORMAT = "%(asctime)-4s | %(levelname)-4s | %(message)s"
logging.basicConfig(
	level=logging.INFO,
	format=LOGFORMAT,
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
		"filter": [
			{"left": "typespecs", "operation": "has", "right": "common"},
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


if __name__ == '__main__':
	path_ = '../'
