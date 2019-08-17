import asynctest
import pymorphy2
import pytest
from aiohttp import InvalidURL, ClientError

from main import process_article, get_charged_words, ProcessingStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def charged_words():
    return get_charged_words()


@pytest.fixture()
def morph():
    return pymorphy2.MorphAnalyzer()


@pytest.fixture()
def session_mock():
    return asynctest.CoroutineMock()


@pytest.fixture()
def fetch_mock():
    return asynctest.CoroutineMock()


async def mock_fetch_errors(*args):
    url = args[1]
    if "invalid_url" in url:
        raise InvalidURL(url)
    elif "client_error" in url:
        raise ClientError


async def test_success_process_article(
    charged_words, morph, fetch_mock, session_mock
):
    fetch_mock.return_value = (
        "<title>test title</title>"
        '<article class="article">test article</article>'
    )

    test_url = f"https://inosmi.ru/test_articlle"

    with asynctest.patch("main.fetch", side_effect=fetch_mock):
        url, status, score, words_count = await process_article(
            session_mock, morph, charged_words, test_url
        )
        assert url == test_url
        assert status == ProcessingStatus.OK
        assert words_count == 2


async def test_non_existing_article_parsing(
    charged_words, morph, fetch_mock, session_mock
):
    broken_url = f"https://nonexistentUrl.com/test_article"
    fetch_mock.return_value = ""

    expected_result = (broken_url, ProcessingStatus.PARSING_ERROR, None, None)
    with asynctest.patch("main.fetch", side_effect=fetch_mock):
        result = await process_article(
            session_mock, morph, charged_words, broken_url
        )
        assert result == expected_result


async def test_invalid_url_error(charged_words, morph, session_mock):
    invalid_url = f"https://inosmi.ru/invalid_url"

    expected_result = (invalid_url, ProcessingStatus.FETCH_ERROR, None, None)

    with asynctest.patch("main.fetch", side_effect=mock_fetch_errors):
        result = await process_article(
            session_mock, morph, charged_words, invalid_url
        )
        assert result == expected_result


async def test_client_error(charged_words, morph, session_mock):
    wrong_client_url = f"https://inosmi.ru/client_error"

    expected_result = (
        wrong_client_url,
        ProcessingStatus.FETCH_ERROR,
        None,
        None,
    )

    with asynctest.patch("main.fetch", side_effect=mock_fetch_errors):
        result = await process_article(
            session_mock, morph, charged_words, wrong_client_url
        )
        assert result == expected_result
