import asyncio

import aiohttp
import aionursery
import pymorphy2
from adapters import SANITIZERS
from aiohttp_socks import SocksConnector
from text_tools import split_by_words, calculate_jaundice_rate

sanitize = SANITIZERS['inosmi_ru']

URL = 'https://inosmi.ru/culture/20190731/245546920.html'

TEST_ARTICLES = [
    ("https://inosmi.ru/social/20190714/245464409.html",
     "Нигилизм национального масштаба: нашу самобытность уничтожают"),
    ("https://inosmi.ru/military/20190806/245591101.html",
     "Америка может проиграть в настоящей войне с Россией"),
    ("https://inosmi.ru/social/20190412/244929181.html",
     "Berlingske (Дания): цвет кожи, предрассудки и слово «негр»"),
    ("https://inosmi.ru/politic/20190802/245567929.html",
     "Yeni Akit (Турция): мир застыл в ожидании учений в Ормузском проливе"),
    ("https://inosmi.ru/politic/20190806/245586424.html",
     "Daily Sabah: Индия намерена лишить Кашмир особого статуса"),
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url, title):
    html = await fetch(session, url)
    clean_plaintext = sanitize(html, plaintext=True)

    article_words = split_by_words(morph, clean_plaintext)
    score = calculate_jaundice_rate(article_words, charged_words)

    return title, score, len(article_words)


def get_charged_words():
    negative_words = [
        line.rstrip('\n') for line in open('charged_dict/negative_words.txt')
    ]
    positive_words = [
        line.rstrip('\n') for line in open('charged_dict/positive_words.txt')
    ]
    return [*negative_words, *positive_words]


async def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words()

    connector = SocksConnector.from_url('socks5://127.0.0.1:9050', rdns=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        async with aionursery.Nursery() as nursery:
            for (url, title) in TEST_ARTICLES:
                # add all child tasks (one task per one article) to general list
                tasks.append(
                    nursery.start_soon(
                        process_article(
                            session, morph, charged_words, url, title
                        )
                    )
                )
            done, pending = await asyncio.wait(tasks)  # run all tasks together

            for future in done:
                title, score, words_count = future.result()
                print('Заголовок:', title)
                print('Рейтинг:', score)
                print('Слов в статье:', words_count)
                print()

asyncio.run(main())
