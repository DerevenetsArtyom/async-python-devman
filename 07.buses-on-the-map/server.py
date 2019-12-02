import contextlib
import json

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


async def handle_simulator(request):
    ws = await request.accept()

    while True:
        try:
            json_message = await ws.get_message()  # "busId","lat","lng","route"
        except ConnectionClosed:
            print("handle_simulator: ConnectionClosed")
            break

        message = json.loads(json_message)
        print("handle_simulator:", message)

        # Update data in global 'buses' for each bus with received info
        buses[message["busId"]] = message
        await trio.sleep(0.1)


async def main():
    browser_host = simulator_host = "127.0.0.1"

    browser_port = 8000  # sends data to the browser through 8000 port
    simulator_port = 8080  # receives data from simulator through 8080 port

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, handle_simulator, simulator_host, simulator_port, None
        )
        nursery.start_soon(
            serve_websocket, listen_browser, browser_host, browser_port, None
        )
        # nursery.start_soon(serve_websocket, talk_to_browser, host, 8000, None)


with contextlib.suppress(KeyboardInterrupt):
    trio.run(main)
