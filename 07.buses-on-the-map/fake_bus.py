import json
import itertools
import random

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed
from utils import generate_bus_id, load_routes


async def run_bus(bus_id, route, send_channel):  # PRODUCER
    message = {"busId": None, "lat": None, "lng": None, "route": None}

    start_offset = random.randrange(len(route["coordinates"]))

    # infinite loop to circle the route (start again after finish)
    while True:
        for coo in route["coordinates"][start_offset:]:
            message["busId"] = bus_id
            message["route"] = route['name']
            message["lat"] = coo[0]
            message["lng"] = coo[1]

            await send_channel.send(message)


async def send_updates(server_address, receive_channel):  # CONSUMER
    # new function to gather and send data

    # TODO: broken - open too many sockets

    async with open_websocket_url(server_address) as ws:
        async for value in receive_channel:
            await ws.send_message(json.dumps(value, ensure_ascii=True))
            await trio.sleep(1)


async def main():
    socket_url = "ws://127.0.0.1:8080"
    buses_per_route = 10
    routes_number = 5
    websockets_number = 5

    mem_channels = []
    for _ in range(websockets_number):
        mem_channels.append(trio.open_memory_channel(0))

    try:
        async with trio.open_nursery() as nursery:

            for bus_index in range(1, buses_per_route + 1):
                for route in itertools.islice(load_routes(), routes_number):

                    bus_id = generate_bus_id(route['name'], bus_index)

                    # Pick random channel for every bus
                    send_channel, receive_channel = random.choice(mem_channels)

                    try:
                        nursery.start_soon(run_bus, bus_id, route, send_channel)
                        nursery.start_soon(
                            send_updates, socket_url, receive_channel
                        )
                    except ConnectionClosed:
                        break

    except OSError as ose:
        print("Connection attempt failed: %s" % ose, file=stderr)


trio.run(main)
