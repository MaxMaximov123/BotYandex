import asyncio
import random
import websocket
import websockets
import logging
import json
import functools
from pprint import pprint
from scripts import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOGFORMAT,
)


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


def merge_dicts(*dicts):
    """
    Рекурсивно объединяет несколько многомерных словарей, массивов словарей и других типов данных.
    :param dicts: Множество словарей и других типов данных, которые нужно объединить.
    :return: Объединенный словарь.
    """
    result = {}
    for dictionary in dicts:
        if isinstance(dictionary, dict):
            for key, value in dictionary.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
        elif isinstance(dictionary, list):
            for item in dictionary:
                if isinstance(item, dict):
                    result = merge_dicts(result, item)
                else:
                    result = result + [item] if isinstance(result, list) else [item]
        else:
            result = dictionary
    return result


def on_message(data, name, ws, message):
    if '{' not in message:
        ws.send(message)
    else:
        msg_list = message.split('~m~')
        for i in msg_list:
            if i and not i.isdigit():
                d = json.loads(i)
                if len(d.get('p', [])) > 1:
                    d = d['p'][1]['v']
                    data[name] = merge_dicts(data[name], d)
        # pprint(data)


def on_error(ws, error):
    logging.warning(error)


def on_close(ws, *close_status_code):
    logging.info(f"WebSocket closed with status code: {close_status_code}")


def on_open(name, key, ws):
    ws.send(
        '~m~636~m~{"m":"set_auth_token","p":["eyJhbGciOiJSUzUxMiIsImtpZCI6IkdaeFUiLCJ0eXAiOiJKV1QifQ.eyJ1c2VyX2lkIjo0NDMwMTYxOCwiZXhwIjoxNjgxNDkxMTcxLCJpYXQiOjE2ODE0NzY3NzEsInBsYW4iOiIiLCJleHRfaG91cnMiOjEsInBlcm0iOiIiLCJzdHVkeV9wZXJtIjoiIiwibWF4X3N0dWRpZXMiOjMsIm1heF9mdW5kYW1lbnRhbHMiOjAsIm1heF9jaGFydHMiOjEsIm1heF9hY3RpdmVfYWxlcnRzIjoxLCJtYXhfYWN0aXZlX3ByaW1pdGl2ZV9hbGVydHMiOjEsIm1heF9hY3RpdmVfY29tcGxleF9hbGVydHMiOjEsIm1heF9zdHVkeV9vbl9zdHVkeSI6MSwibWF4X2Nvbm5lY3Rpb25zIjoyfQ.R5U9TgWcGzTYj_tAGekedcwOD-K65_UA-zLpXSO1kty9xIc_WhwMHEIloR2MGUhptnYDeF0YRO1YKFpLD_kCG5lQMQmw3fJ_dKp-32lmVQ5KCvkO1bVqAiI-Sn1xKN34NilxG7arVfPDmYkdKeNFeYXySY4WKcYhKaDD4y2WAi0"]}')
    ws.send('~m~34~m~{"m":"set_locale","p":["ru","RU"]}')
    ws.send('~m~52~m~{"m":"quote_create_session","p":["' + key + '"]}')

    ws.send(
        '~m~735~m~{"m":"quote_set_fields","p":["' + key + '","base-currency-logoid","ch","chp","currency-logoid","currency_code","currency_id","base_currency_id","current_session","description","exchange","format","fractional","is_tradable","language","local_description","listed_exchange","logoid","lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","typespecs","update_mode","volume","value_unit_id","ask","bid","fundamentals","high_price","is_tradable","low_price","open_price","prev_close_price","rch","rchp","rtc","rtc_time","status","basic_eps_net_income","beta_1_year","earnings_per_share_basic_ttm","industry","market_cap_basic","price_earnings_ttm","sector","volume","dividends_yield","timezone"]}')
    ws.send('~m~' + str(52 + len(name)) + '~m~{"m":"quote_add_symbols","p":["' + key + '","' + name + '"]}')


def subscribe_on_stock(name, data):
    data[name] = {}
    s = list('abcdefghijklmnopqrstuvwxyz' + 'abcdefghijklmnopqrstuvwxyz'.upper() + '1234567890')
    random.shuffle(s)
    key = 'qs_' + ''.join(random.choices(s, k=12))
    # key = 'qs_8UTPLjgwedqk'
    ws = websocket.WebSocketApp(
        "wss://data.tradingview.com/socket.io/websocket",
        on_message=functools.partial(on_message, data, name),
        on_error=on_error,
        on_close=on_close,
        on_open=functools.partial(on_open, name, key)
    )
    ws.run_forever()


if __name__ == "__main__":
    subscribe_on_stock("NASDAQ:AAPL", {})
    # asyncio.run(websocket_connect1())
