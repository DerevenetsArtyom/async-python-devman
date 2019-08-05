import asyncio

import aiohttp
import pymorphy2
from aiohttp_socks import SocksConnector

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate


URL = 'https://inosmi.ru/culture/20190731/245546920.html'

sanitize = SANITIZERS['inosmi_ru']


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    # connector = SocksConnector.from_url('socks5://127.0.0.1:9050', rdns=True)
    # async with aiohttp.ClientSession(connector=connector) as session:
    #     html = await fetch(session, URL)
    #     clean_plaintext = sanitize(html, plaintext=True)
    #     print(clean_plaintext)

    morph = pymorphy2.MorphAnalyzer()

    with open('text.txt') as f:
        html = f.read()

    clean_plaintext = sanitize(html, plaintext=True)
    article_words = split_by_words(morph, clean_plaintext)

    negative_words = [
        line.rstrip('\n') for line in open('charged_dict/negative_words.txt')
    ]
    positive_words = [
        line.rstrip('\n') for line in open('charged_dict/positive_words.txt')
    ]
    full_list = [*negative_words, *positive_words]

    print('Words in article', len(article_words))
    print('Rating', calculate_jaundice_rate(article_words, full_list))


asyncio.run(main())
