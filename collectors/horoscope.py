import requests
from bs4 import BeautifulSoup as BS


def get(url):
    r = requests.get(url)
    html = BS(r.content, "html.parser")

    soup1 = html.select('h1')[0].text
    soup = html.select('p')
    return soup1, soup