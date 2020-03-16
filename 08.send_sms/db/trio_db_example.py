import functools
import asyncio
import warnings

import aioredis
import argparse

import trio
from trio import TrioDeprecationWarning

import trio_asyncio

from db import Database

warnings.filterwarnings("ignore", category=TrioDeprecationWarning)


def create_argparser():
    parser = argparse.ArgumentParser(description="Redis database usage example")
    parser.add_argument("--address", action="store", dest="redis_uri", default="redis://127.0.0.1:6379")
    return parser


async def main():
    # trio_asyncio has difficulties with aioredis, workaround here:
    # https://github.com/python-trio/trio-asyncio/issues/63 (answer from @parity3)
    asyncio._set_running_loop(asyncio.get_event_loop())

    parser = create_argparser()
    args = parser.parse_args()

    # WAS BEFORE: redis = await aioredis.create_redis_pool(args.redis_uri, encoding='utf-8')
    create_redis_pool = functools.partial(aioredis.create_redis_pool, encoding="utf-8")
    redis = await trio_asyncio.run_asyncio(create_redis_pool, args.redis_uri)

    try:
        db = Database(redis)

        sms_id = "1"

        phones = [
            "+7 999 519 05 57",
            "911",
            "112",
        ]
        text = "Вечером будет шторм!"

        # WAS BEFORE: await db.add_sms_mailing(...)
        await trio_asyncio.run_asyncio(db.add_sms_mailing, sms_id, phones, text)

        # WAS BEFORE: sms_ids = await db.list_sms_mailings()
        sms_ids = await trio_asyncio.run_asyncio(db.list_sms_mailings)
        print("Registered mailings ids", sms_ids)

        # WAS BEFORE: pending_sms_list = await db.get_pending_sms_list()
        pending_sms_list = await trio_asyncio.run_asyncio(db.get_pending_sms_list)
        print("pending:")
        print(pending_sms_list)

        # WAS BEFORE: await db.update_sms_status_in_bulk([ ... ])
        await trio_asyncio.run_asyncio(
            db.update_sms_status_in_bulk,
            [
                # [sms_id, phone_number, status]
                [sms_id, "112", "failed"],
                [sms_id, "911", "pending"],
                [sms_id, "+7 999 519 05 57", "delivered"],
                # following statuses are available: failed, pending, delivered
            ],
        )

        # WAS BEFORE: pending_sms_list = await db.get_pending_sms_list()
        pending_sms_list = await trio_asyncio.run_asyncio(db.get_pending_sms_list)
        print("pending:")
        print(pending_sms_list)

        # WAS BEFORE: sms_mailings = await db.get_sms_mailings('1')
        sms_mailings = await trio_asyncio.run_asyncio(db.get_sms_mailings, "1")
        print("sms_mailings")
        print(sms_mailings)

        async def send():
            while True:
                # WAS BEFORE: await asyncio.sleep(1)
                await trio.sleep(1)

                # WAS BEFORE: await redis.publish('updates', sms_id)
                await trio_asyncio.run_asyncio(redis.publish, "updates", sms_id)

        async def listen():
            # WAS BEFORE: *_, channel = await redis.subscribe('updates')
            *_, channel = await trio_asyncio.run_asyncio(redis.subscribe, "updates")

            while True:
                # WAS BEFORE: raw_message = await channel.get()
                raw_message = await trio_asyncio.run_asyncio(channel.get)

                if not raw_message:
                    raise ConnectionError("Connection was lost")

                message = raw_message.decode("utf-8")
                print("Got message:", message)

        # WAS BEFORE: await asyncio.gather(send(), listen())
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send)
            nursery.start_soon(listen)

    finally:
        redis.close()
        # WAS BEFORE: await redis.wait_closed()
        await trio_asyncio.run_asyncio(redis.wait_closed)


if __name__ == "__main__":
    trio_asyncio.run(main)
