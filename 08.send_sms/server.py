import asyncio
import functools
import warnings
from contextlib import suppress

import aioredis
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig
import trio
from quart import websocket, request
from dotenv import load_dotenv
import json
import os

from quart_trio import QuartTrio
import trio_asyncio

from main import request_smsc
from db.db import Database

app = QuartTrio(__name__)


@app.before_serving
async def create_db_pool():
    """Create and bind db_pool before start serving requests"""
    create_redis_pool = functools.partial(aioredis.create_redis_pool, encoding='utf-8')

    redis_uri = "redis://127.0.0.1:6379"

    redis = await trio_asyncio.run_asyncio(create_redis_pool, redis_uri)
    app.db_pool = Database(redis)


@app.after_serving
async def close_db_pool():
    if app.db_pool:
        app.db_pool.redis.close()
        await trio_asyncio.run_asyncio(app.db_pool.redis.wait_closed)


@app.route('/', methods=["GET"])
async def index():
    return await app.send_static_file("index.html")


@app.route('/send/', methods=['POST'])
async def send():
    # load_dotenv()
    # login = os.getenv("LOGIN")
    # password = os.getenv("PASSWORD")
    # phone = os.getenv("PHONE")
    # res = await request_smsc('send', login, password, {"phones": phone}, message)
    import random

    sms_id = str(random.randint(1, 10))
    phones = ["911", "112"]
    form = await request.form
    message = form["text"]

    await trio_asyncio.run_asyncio(app.db_pool.add_sms_mailing, sms_id, phones, message)

    sms_ids = await trio_asyncio.run_asyncio(app.db_pool.list_sms_mailings)
    print('There are sms with such IDs in the DB', sms_ids)

    print('sms_mailings:')
    for id in sms_ids:
        sms_mailings = await trio_asyncio.run_asyncio(app.db_pool.get_sms_mailings, id)
        print('\t', sms_mailings)
    print()

    return {}


@app.websocket('/ws')
async def ws():
    message = {
        "msgType": "SMSMailingStatus",
        "SMSMailings": [
            {
                "timestamp": 1123131392.734,
                "SMSText": "Сегодня гроза! Будьте осторожны!",
                "mailingId": "1",
                "totalSMSAmount": 100,
                "deliveredSMSAmount": 0,
                "failedSMSAmount": 5,
            }
        ]
    }

    while True:
        for i in range(100):
            message["SMSMailings"][0]["deliveredSMSAmount"] = i
            await websocket.send(json.dumps(message))
            await trio.sleep(1)


async def run_server():
    async with trio_asyncio.open_loop():
        # trio_asyncio has difficulties with aioredis, workaround here:
        # https://github.com/python-trio/trio-asyncio/issues/63 (answer from @parity3)
        asyncio._set_running_loop(asyncio.get_event_loop())

        config = HyperConfig()
        config.bind = [f"0.0.0.0:5000"]
        config.use_reloader = True
        app.static_folder = 'frontend'
        await serve(app, config)


if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=trio.TrioDeprecationWarning)
    with suppress(KeyboardInterrupt):
        trio.run(run_server)
