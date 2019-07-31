import asyncio

import aiohttp
from aiohttp_socks import SocksConnector

URL = 'https://inosmi.ru/culture/20190731/245546920.html'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    connector = SocksConnector.from_url('socks5://127.0.0.1:9050', rdns=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        html = await fetch(session, URL)
        print(html)


asyncio.run(main())
