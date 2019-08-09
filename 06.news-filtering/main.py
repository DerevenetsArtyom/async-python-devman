import asyncio
import time
from enum import Enum

from aiohttp import web
import functools

import aiohttp
import aionursery
import async_timeout
import pymorphy2
from adapters import SANITIZERS, ArticleNotFound
from aiohttp_socks import SocksConnector, SocksError
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


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def fetch(session, url):
    async with async_timeout.timeout(5):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()


async def process_article(session, morph, charged_words, url, title):
    try:
        html = await fetch(session, url)
        link_fetched = True
        status = ProcessingStatus.OK
        clean_plaintext = sanitize(html, plaintext=True)

    except (SocksError, aiohttp.ClientError):
        link_fetched = False
        status = ProcessingStatus.FETCH_ERROR
        title = 'URL does not exist'

    except ArticleNotFound:
        link_fetched = False
        status = ProcessingStatus.PARSING_ERROR
        title = 'Adapter does not exist'

    except asyncio.TimeoutError:
        link_fetched = False
        status = ProcessingStatus.TIMEOUT

    # TODO: make that with custom context manager
    start = time.monotonic()

    if link_fetched:
        try:
            article_words = await split_by_words(morph, clean_plaintext)
            words_count = len(article_words)
            score = calculate_jaundice_rate(article_words, charged_words)
        except asyncio.TimeoutError:
            status = ProcessingStatus.TIMEOUT
            words_count = score = None
    else:
        words_count = score = None

    end = time.monotonic()
    time_taken = round(end - start, 2)

    return title, status, score, words_count, time_taken


def get_charged_words():
    negative_words = [
        line.rstrip('\n') for line in open('charged_dict/negative_words.txt')
    ]
    positive_words = [
        line.rstrip('\n') for line in open('charged_dict/positive_words.txt')
    ]
    return [*negative_words, *positive_words]


async def main():
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
                title, status, score, words_count, time_taken = future.result()
                print('Заголовок:', title)
                print('Статус:', status)
                print('Рейтинг:', score)
                print('Слов в статье:', words_count)
                print('Analysis took', time_taken)
                print()


asyncio.run(main())


async def articles_handler(morph, charged_words, request):
    # http://127.0.0.1?urls=https://ya.ru,https://google.com
    # {'urls': ['https://ya.ru', 'https://google.com']}

    urls = request.rel_url.query['urls']
    data = {"urls": urls.split(',')}

    # await main(urls)

    return web.json_response(data)


def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words()

    app = web.Application()
    app.add_routes([
        web.get('/', functools.partial(articles_handler, morph, charged_words)),
    ])

    web.run_app(app)


if __name__ == "__main__":
    main()
