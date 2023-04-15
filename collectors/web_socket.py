import websocket
import logging
import json
import functools
from pprint import pprint
from scripts import config

logging.basicConfig(
	level=config.LOG_LEVEL,
	format=config.LOGFORMAT,
)

data = {}


def iter_(obj):
	if type(obj) == dict:
		return obj.items()
	elif type(obj) == list:
		return enumerate(obj)


def list_to_dict(obj):
	d = {}
	for i, val in iter_(obj):
		d[i] = val
	return d


def merge_dict(dict1, dict2):
	dict1 = list_to_dict(dict1)
	dict2 = list_to_dict(dict2)
	# pprint(dict2)
	for key, val in dict1:
		dict1[key] = list_to_dict(dict1[key])
		if key in dict2:
			dict2[key] = list_to_dict(dict2[key])
		if type(val) == dict:
			if key in dict2 and type(dict2[key]) == dict:
				dict1[key] = merge_dict(dict1[key], dict2[key])
		elif key in dict2:
			dict1[key] = dict2[key]
	for key, val in dict2.items():
		if key not in dict1:
			dict1[key] = val
	return dict1


def on_message(ws, message):
	global data
	loc_data = {}
	if '{' not in message:
		ws.send(message)
	else:
		msg_list = message.split('~m~')
		for i in msg_list:
			if i and not i.isdigit():
				d = json.loads(i)
				# pprint(d)
				loc_data = merge_dict(loc_data, d)
	data = merge_dict(data, loc_data)
	pprint(data)


# pprint(data)


def on_error(ws, error):
	logging.warning(error)


def on_close(ws, *close_status_code):
	logging.info("WebSocket closed with status code:", close_status_code)


def on_open(name, ws):
	ws.send(
		"""~m~636~m~{"m":"set_auth_token","p":["eyJhbGciOiJSUzUxMiIsImtpZCI6IkdaeFUiLCJ0eXAiOiJKV1QifQ.eyJ1c2VyX2lkIjo0NDMwMTYxOCwiZXhwIjoxNjgxNDkxMTcxLCJpYXQiOjE2ODE0NzY3NzEsInBsYW4iOiIiLCJleHRfaG91cnMiOjEsInBlcm0iOiIiLCJzdHVkeV9wZXJtIjoiIiwibWF4X3N0dWRpZXMiOjMsIm1heF9mdW5kYW1lbnRhbHMiOjAsIm1heF9jaGFydHMiOjEsIm1heF9hY3RpdmVfYWxlcnRzIjoxLCJtYXhfYWN0aXZlX3ByaW1pdGl2ZV9hbGVydHMiOjEsIm1heF9hY3RpdmVfY29tcGxleF9hbGVydHMiOjEsIm1heF9zdHVkeV9vbl9zdHVkeSI6MSwibWF4X2Nvbm5lY3Rpb25zIjoyfQ.R5U9TgWcGzTYj_tAGekedcwOD-K65_UA-zLpXSO1kty9xIc_WhwMHEIloR2MGUhptnYDeF0YRO1YKFpLD_kCG5lQMQmw3fJ_dKp-32lmVQ5KCvkO1bVqAiI-Sn1xKN34NilxG7arVfPDmYkdKeNFeYXySY4WKcYhKaDD4y2WAi0"]}""")
	ws.send("""~m~34~m~{"m":"set_locale","p":["ru","RU"]}""")
	ws.send("""~m~52~m~{"m":"quote_create_session","p":["qs_nB1SeES5SN7O"]}""")

	ws.send(
		"""~m~735~m~{"m":"quote_set_fields","p":["qs_nB1SeES5SN7O","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","value_unit_id","ask","bid","fundamentals","high_price","is_tradable","low_price","open_price","prev_close_price","rch","rchp","rtc","rtc_time","status","basic_eps_net_income","beta_1_year","earnings_per_share_basic_ttm","industry","market_cap_basic","price_earnings_ttm","sector","volume","dividends_yield","timezone"]}""")
	ws.send('''~m~61~m~{"m":"quote_add_symbols","p":["qs_nB1SeES5SN7O","''' + name + '''"]}''')


def subscribe_on_stock(name):
	ws = websocket.WebSocketApp(
		"wss://data.tradingview.com/socket.io/websocket",
		on_message=on_message,
		on_error=on_error,
		on_close=on_close,
		on_open=functools.partial(on_open, name)
	)
	ws.run_forever()


if __name__ == "__main__":
	subscribe_on_stock("MOEX:SBER")
