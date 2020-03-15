import functools

import aioredis
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig
import trio
from quart import websocket, render_template, request
from dotenv import load_dotenv
import json
import os

from quart_trio import QuartTrio
import trio_asyncio

from main import request_smsc
from db.db import Database

app = QuartTrio(__name__, template_folder='frontend')


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


@app.route('/')
async def hello():
    context = {
        "date": "01.02.2000",
        "mailingId": "33",
        "SMSText": "SMSText",
        "percentFulfilled": "33",
        "percentFailed": "11",
    }
    return await render_template('index.html', mailing=context)


@app.route('/send/', methods=['POST'])
async def send():
    load_dotenv()

    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    phone = os.getenv("PHONE")

    form = await request.form
    message = form["text"]
    res = await request_smsc('send', login, password, {"phones": phone}, message)
    print('res', res)
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


app.run('0.0.0.0', port=5000)
