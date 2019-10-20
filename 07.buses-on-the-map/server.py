import json
import functools

import trio
from trio_websocket import serve_websocket, ConnectionClosed

message_to_browser = {
    "msgType": "Buses",
    "buses": [
        # {"busId": None, "lat": None, "lng": None, "route": None},
    ],
}


BUSES = {}  # global variable to collect buses info -  {bus_id: bus_info}


async def talk_to_browser(request):
    ws = await request.accept()
    while True:
        message_to_browser["buses"] = list(BUSES.values())
        msg = json.dumps(message_to_browser)
        try:
            print("talk_to_browser:", msg)
            await ws.send_message(msg)
        except ConnectionClosed:
            print("talk_to_browser: ConnectionClosed")
            break

        await trio.sleep(1)


async def receive_from_fake(request):
    ws = await request.accept()

    while True:
        try:
            json_message = await ws.get_message()  # "busId","lat","lng","route"
        except ConnectionClosed:
            print("receive_from_fake: ConnectionClosed")
            break

        message = json.loads(json_message)
        print("receive_from_fake:", message)

        # Update data in global BUSES for each bus with received info
        BUSES[message["busId"]] = message
        await trio.sleep(0.1)


async def main():
    """
    Script receives data from simulator through 8080 port,
    and sends it to the browser through 8000 port.
    """

    host = "127.0.0.1"

    receive_from_fake_coro = functools.partial(
        serve_websocket, receive_from_fake, host, 8080, ssl_context=None
    )
    talk_to_browser_coro = functools.partial(
        serve_websocket, talk_to_browser, host, 8000, ssl_context=None
    )

    async with trio.open_nursery() as nursery:
        nursery.start_soon(receive_from_fake_coro)
        nursery.start_soon(talk_to_browser_coro)


trio.run(main)
