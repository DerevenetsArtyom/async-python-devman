import asyncio

import aiohttp
from aiohttp_socks import SocksConnector

from adapters import SANITIZERS

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

    with open('text.txt') as f:
        html = f.read()
        clean_plaintext = sanitize(html, plaintext=True)
        print(clean_plaintext)


asyncio.run(main())
