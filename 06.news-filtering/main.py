import asyncio
import functools
from enum import Enum

import aiohttp
import aionursery
import async_timeout
import pymorphy2
from adapters import SANITIZERS, ArticleNotFound
from aiohttp import web
from aiohttp_socks import SocksConnector, SocksError
from text_tools import split_by_words, calculate_jaundice_rate

sanitize = SANITIZERS["inosmi_ru"]

TEST_ARTICLES = [
    (
        "https://inosmi.ru/social/20190714/245464409.html",
        "Нигилизм национального масштаба: нашу самобытность уничтожают",
    ),
    (
        "https://inosmi.ru/military/20190806/245591101.html",
        "Америка может проиграть в настоящей войне с Россией",
    ),
    (
        "https://inosmi.ru/social/20190412/244929181.html",
        "Berlingske (Дания): цвет кожи, предрассудки и слово «негр»",
    ),
    (
        "https://inosmi.ru/politic/20190802/245567929.html",
        "Yeni Akit (Турция): мир застыл в ожидании учений в Ормузском проливе",
    ),
    (
        "https://inosmi.ru/politic/20190806/245586424.html",
        "Daily Sabah: Индия намерена лишить Кашмир особого статуса",
    ),
]


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


async def fetch(session, url):
    async with session.get(url, raise_for_status=True, timeout=6) as response:
        return await response.text()


async def process_article(session, morph, charged_words, url):
    try:
        html = await fetch(session, url)
        link_fetched = True
        status = ProcessingStatus.OK
        clean_plaintext = sanitize(html, plaintext=True)

    except (SocksError, aiohttp.ClientError):
        link_fetched = False
        status = ProcessingStatus.FETCH_ERROR

    except ArticleNotFound:
        link_fetched = False
        status = ProcessingStatus.PARSING_ERROR

    except asyncio.TimeoutError:
        link_fetched = False
        status = ProcessingStatus.TIMEOUT

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

    return url, status, score, words_count


def get_charged_words():
    with open("charged_dict/negative_words.txt") as f:
        negative_words = [line.rstrip("\n") for line in f]

    with open("charged_dict/positive_words.txt") as f:
        positive_words = [line.rstrip("\n") for line in f]

    return [*negative_words, *positive_words]


async def get_parsed_articles(morph, charged_words, urls):
    # Can't connect directly because of blocked site, use TOR
    connector = SocksConnector.from_url("socks5://127.0.0.1:9050", rdns=True)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        async with aionursery.Nursery() as nursery:
            for url in urls:
                # add all child tasks (one task per one article) to general list
                tasks.append(
                    nursery.start_soon(
                        process_article(session, morph, charged_words, url)
                    )
                )
            done, pending = await asyncio.wait(tasks)  # run all tasks together

            results = []

            for future in done:
                url, status, score, words_count = future.result()
                results.append(
                    {
                        "status": status.value,
                        "url": url,
                        "score": score,
                        "words_count": words_count,
                    }
                )

    return results


async def articles_handler(morph, charged_words, request):
    urls_params = request.rel_url.query.get("urls")
    if not urls_params:
        return web.json_response(data={"error": "no one urls"}, status=400)

    urls_list = urls_params.split(",")

    if len(urls_list) > 10:
        return web.json_response(
            data={"error": "too many urls in request, should be 10 or less"},
            status=400,
        )

    result_data = await get_parsed_articles(morph, charged_words, urls_list)

    return web.json_response(data=result_data)


def main():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words()

    app = web.Application()
    app.add_routes(
        [
            web.get(
                "/", functools.partial(articles_handler, morph, charged_words)
            )
        ]
    )

    web.run_app(app)


if __name__ == "__main__":
    main()
