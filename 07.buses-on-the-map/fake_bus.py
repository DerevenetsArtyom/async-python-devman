import os
import json
import itertools

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed

message = {
    "busId": None, "lat": None, "lng": None, "route": None
}


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, route):
    async with open_websocket_url(url) as ws:
        for coo in route["coordinates"]:
            message["busId"] = route['name']
            message["lat"] = coo[0]
            message["lng"] = coo[1]
            message["route"] = route['name']

            await ws.send_message(json.dumps(message, ensure_ascii=True))

            await trio.sleep(0.5)


async def main():
    socket_url = 'ws://127.0.0.1:8080'
    try:
        async with trio.open_nursery() as nursery:
            for route in itertools.islice(load_routes(), 10):
                try:
                    nursery.start_soon(run_bus, socket_url, route)
                except ConnectionClosed:
                    break

    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


trio.run(main)
