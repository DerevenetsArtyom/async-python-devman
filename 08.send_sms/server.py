import os
import random
import asyncio
import functools
import warnings
from contextlib import suppress
from typing import Dict, Any

import aioredis
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig
import trio
from quart import websocket, request, Response
import json

from quart_trio import QuartTrio
import trio_asyncio

from db.db import Database
from utils import convert_sms_data

app = QuartTrio(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", '127.0.0.1')
REDIS_PORT = os.getenv("REDIS_PORT", 6379)


@app.before_serving
async def create_db_pool() -> None:
    """Create and bind db_pool before start serving requests"""
    create_redis_pool = functools.partial(aioredis.create_redis_pool, encoding="utf-8")

    redis_uri = f"redis://{REDIS_HOST}:{REDIS_PORT}"

    redis = await trio_asyncio.run_asyncio(create_redis_pool, redis_uri)
    app.db_pool = Database(redis)


@app.after_serving
async def close_db_pool() -> None:
    if app.db_pool:
        app.db_pool.redis.close()
        await trio_asyncio.run_asyncio(app.db_pool.redis.wait_closed)


@app.route("/", methods=["GET"])
async def index() -> Response:
    return await app.send_static_file("index.html")


@app.route("/send/", methods=["POST"])
async def send_sms() -> Dict[str, Any]:
    # Neither 'request_smsc' nor mocked stuff is used here,
    # just static data with some random for sake of simplicity

    sms_id = str(random.randint(1, 10))
    form = await request.form
    message = form["text"]

    await trio_asyncio.run_asyncio(app.db_pool.add_sms_mailing, sms_id, ["911", "112"], message)

    sms_ids = await trio_asyncio.run_asyncio(app.db_pool.list_sms_mailings)
    print("There are messages with such IDs in the DB:", sms_ids)

    print("sms_mailings:")
    for id in sms_ids:
        sms_mailings = await trio_asyncio.run_asyncio(app.db_pool.get_sms_mailings, id)
        print("\t", sms_mailings)
    print()

    return {}


@app.websocket("/ws")
async def ws() -> None:
    while True:
        all_sms_ids = await trio_asyncio.run_asyncio(app.db_pool.list_sms_mailings)
        all_sms_data = await trio_asyncio.run_asyncio(app.db_pool.get_sms_mailings, *all_sms_ids)

        sms_list = []
        for sms_data in all_sms_data:
            converted_sms = await convert_sms_data(sms_data)
            sms_list.append(converted_sms)

        response = {
            "msgType": "SMSMailingStatus",
            "SMSMailings": sms_list
        }
        await websocket.send(json.dumps(response))
        await trio.sleep(1)


async def run_server() -> None:
    async with trio_asyncio.open_loop():
        # trio_asyncio has difficulties with aioredis, workaround here:
        # https://github.com/python-trio/trio-asyncio/issues/63 (answer from @parity3)
        asyncio._set_running_loop(asyncio.get_event_loop())

        config = HyperConfig()
        config.bind = [f"0.0.0.0:5000"]
        config.use_reloader = True
        app.static_folder = "frontend"
        await serve(app, config)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=trio.TrioDeprecationWarning)
    with suppress(KeyboardInterrupt):
        trio.run(run_server)
