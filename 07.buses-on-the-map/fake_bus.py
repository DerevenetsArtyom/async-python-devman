import os
import json
import itertools
import random

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed


def load_routes(directory_path="routes"):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, "r", encoding="utf8") as file:
                yield json.load(file)


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


async def run_bus(url, bus_id, route):
    message = {
        "busId": None, "lat": None, "lng": None, "route": None
    }

    async with open_websocket_url(url) as ws:
        # infinite loop to circle the route (start again after finish)
        while True:
            for coo in route["coordinates"]:
                message["busId"] = bus_id
                message["route"] = bus_id
                message["lat"] = coo[0]
                message["lng"] = coo[1]

                await ws.send_message(json.dumps(message, ensure_ascii=True))
                await trio.sleep(1)


async def main():
    socket_url = "ws://127.0.0.1:8080"
    buses_per_route = 5

    try:
        async with trio.open_nursery() as nursery:

            for bus_index in range(1, buses_per_route + 1):
                for route in itertools.islice(load_routes(), 10):

                    bus_id = generate_bus_id(route['name'], bus_index)
                    start_offset = random.randrange(len(route["coordinates"]))
                    route["coordinates"] = route["coordinates"][start_offset:]

                    try:
                        nursery.start_soon(run_bus, socket_url, bus_id, route)
                    except ConnectionClosed:
                        break

    except OSError as ose:
        print("Connection attempt failed: %s" % ose, file=stderr)


trio.run(main)
