from pprint import pprint

import requests
import xml.etree.ElementTree as ET


def get():
	response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
	tree = ET.fromstring(response.content)
	markets = {}
	for valute in tree.findall('Valute'):
		markets[valute.find('CharCode').text] = {
			'val': float(
				valute.find('Value').text.replace(',', '.')) / float(
				valute.find('Nominal').text.replace(',', '.')),
			'name': valute.find('Name').text
		}
	return markets


if __name__ == '__main__':
	pprint(get())
