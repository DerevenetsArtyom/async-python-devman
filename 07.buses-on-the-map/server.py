import contextlib
import json
import functools

import trio
from trio_websocket import serve_websocket, ConnectionClosed

buses = {}  # global variable to collect buses info -  {bus_id: bus_info}


async def talk_to_browser(request):
    message_to_browser = {
        "msgType": "Buses",
        # {"busId": None, "lat": None, "lng": None, "route": None},
        "buses": [],
    }
    ws = await request.accept()
    while True:
        message_to_browser["buses"] = list(buses.values())
        msg = json.dumps(message_to_browser)
        try:
            print("talk_to_browser:", msg)
            await ws.send_message(msg)
        except ConnectionClosed:
            print("talk_to_browser: ConnectionClosed")
            break

        await trio.sleep(1)


def is_inside(bounds, lat, lng):
    if bounds['south_lat'] < lat < bounds['north_lat']:
        if bounds['west_lng'] < lng < bounds['east_lng']:
            print('INSIDE')
            return True
    return False


async def listen_browser(request):
    """Receive a message with window coordinates from browser"""

    ws = await request.accept()

    while True:
        try:
            json_message = await ws.get_message()
        except ConnectionClosed:
            print("listen_browser: ConnectionClosed")
            break

        message = json.loads(json_message)
        print("listen_browser:", message)

        inside = []
        bounds = message['data']
        for bus_id, bus_info in buses.items():
            if is_inside(bounds, bus_info["lat"], bus_info["lng"]):
                inside.append({bus_id: bus_info})
                print('inside', len(inside))


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

        # Update data in global 'buses' for each bus with received info
        buses[message["busId"]] = message
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
    listen_browser_coro = functools.partial(
        serve_websocket, listen_browser, host, 8000, ssl_context=None
    )

    async with trio.open_nursery() as nursery:
        nursery.start_soon(receive_from_fake_coro)
        # nursery.start_soon(talk_to_browser_coro)
        nursery.start_soon(listen_browser_coro)


with contextlib.suppress(KeyboardInterrupt):
    trio.run(main)
