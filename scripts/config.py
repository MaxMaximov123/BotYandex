import datetime
import logging
import os
from decouple import config


BETA_TOKEN = config("BETA_TOKEN")
REALISE_TOKEN = config("REALISE_TOKEN")

LOG_LEVEL = logging.INFO
LOGFORMAT = "%(asctime)-4s | %(levelname)-4s | %(message)s"

SEND_TIME = datetime.time(hour=4, minute=0, second=0)

HEADERS_TO_NEWS = {
	'cookie': 'sso_checked=1; Session_id=3:1663433035.5.0.1663433035738:6xZlBQ:20D.1.2:1|883187617.0.2|64:10003835.681836.xnGm7GifGL7Ca51K8l0VpzizisI; yandex_login=maxss.k2n; yandexuid=1979425991640958970; mda2_beacon=1663433035749; gdpr=0; _ym_d=1663433038; _ym_uid=16634330381069804080; vid=e8d0a90e328f8d78; tmr_lvid=4b172abb4997249b25454fd3166bb785; tmr_lvidTS=1664709380222; _yasc=8ScIIJd6joNRWrZw+Sqjf0f5NjkpTbuWeoNd7pRyT4ngVS01bXdy2C5/jgLV; zen_sso_checked=1; vsd=eyJnZW8iOiIxODgiLCJ1YSI6IllBQlJPV1NFUiIsImVhIjozMCwiZWciOjJ9; _ym_isad=2; tmr_detect=0%7C1677143581052',
	'user-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 YaBrowser/23.1.3.949 Yowser/2.5 Safari/537.36',
}

zodiac_signs_links = {
	"Овен♈️": "https://horo.mail.ru/prediction/aries/today/",
	"Телец♉️": "https://horo.mail.ru/prediction/taurus/today/",
	"Близнецы♊️": "https://horo.mail.ru/prediction/gemini/today/",
	"Рак♋️": "https://horo.mail.ru/prediction/cancer/today/",
	"Лев♌️": "https://horo.mail.ru/prediction/leo/today/",
	"Дева♍️": "https://horo.mail.ru/prediction/virgo/today/",
	"Весы♎️": "https://horo.mail.ru/prediction/libra/today/",
	"Скорпион♏️": "https://horo.mail.ru/prediction/scorpio/today/",
	"Стрелец♐️": "https://horo.mail.ru/prediction/sagittarius/today/",
	"Козерог♑️": "https://horo.mail.ru/prediction/capricorn/today/",
	"Водолей♒️": "https://horo.mail.ru/prediction/aquarius/today/",
	"Рыбы♓️": "https://horo.mail.ru/prediction/pisces/today/"
}

NEWS_URLS = {
	'Глвное❗': "https://dzen.ru/news",
	'Мир🌏': 'https://dzen.ru/news/rubric/world',
	'Экономика📈': "https://dzen.ru/news/rubric/business",
	'Политика🇺🇳': "https://dzen.ru/news/rubric/politics",
	'Происшествия🚨': "https://dzen.ru/news/rubric/incident",
	'Казань🕌': "https://dzen.ru/news/region/kazan",
	'Технологии💻': "https://dzen.ru/news/rubric/computers",
	'Спорт⚽️': "https://dzen.ru/news/rubric/sport",
	'МоскваⓂ': 'https://dzen.ru/news/region/moscow',
	'Интересное❔': 'https://dzen.ru/news/rubric/personal_feed',
	'Коронавирус🦠': "https://dzen.ru/news/rubric/koronavirus",
	'Общество👥': 'https://dzen.ru/news/rubric/society',
	'Культура🎨': "https://dzen.ru/news/rubric/culture",
	'Авто🚗': 'https://dzen.ru/news/rubric/auto'
}


COUNTRIES = [
	'america', 'argentina', 'bahrain', 'belgium',
	'brazil', 'uk', 'hungary', 'venezuela',
	'vietnam', 'germany', 'hongkong', 'greece',
	'denmark', 'egypt', 'israel', 'india',
	'indonesia', 'iceland', 'spain', 'italy',
	'canada', 'qatar', 'china', 'colombia',
	'latvia', 'lithuania', 'luxembourg', 'malaysia',
	'mexico', 'nigeria', 'netherlands', 'newzealand',
	'norway', 'uae', 'peru', 'poland',
	'portugal', 'russia', 'romania', 'ksa',
	'serbia', 'singapore', 'slovakia', 'thailand',
	'taiwan', 'turkey', 'philippines', 'finland',
	'france', 'chile', 'switzerland', 'sweden',
	'estonia', 'rsa', 'korea', 'japan'
]
REV_NEWS_URLS = dict([tuple(reversed(i)) for i in NEWS_URLS.items()])
