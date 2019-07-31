import aiohttp
import asyncio

# Links to check to setup TOR connection:
# https://jarroba.com/anonymous-scraping-by-tor-network/
# https://www.sylvaindurand.org/use-tor-with-python/
# https://stackoverflow.com/questions/30286293/make-requests-using-python-over-tor
# http://qaru.site/questions/7264187/how-to-use-socks-proxies-to-make-requests-with-aiohttp
# https://stackoverflow.com/questions/55191914/how-to-connect-to-onion-sites-using-python-aiohttp
# https://gist.github.com/keepitsimple/1de1306a396d5534d7f3302e606ba72a

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
