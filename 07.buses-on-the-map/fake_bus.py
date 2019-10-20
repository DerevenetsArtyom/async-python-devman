import json
import itertools
import random
import asyncclick as click

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
            message["route"] = route["name"]
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


# v — настройка логирования
@click.command()
@click.option(
    "--server",
    default="ws://127.0.0.1:8080",
    show_default=True,
    type=str,
    help="Server address",
)
@click.option(
    "--routes_number",
    default=5,
    show_default=True,
    type=int,
    help="Amount of routes",
)
@click.option(
    "--buses_per_route",
    default=5,
    show_default=True,
    type=int,
    help="Amount of buses per route",
)
@click.option(
    "--websockets_number",
    default=5,
    show_default=True,
    type=int,
    help="Amount of opened websockets",
)
@click.option(
    "--emulator_id",
    default="",
    type=str,
    show_default=True,
    help="Prefix to 'busId' in case of several instances fake_bus.py",
)
@click.option(
    "--refresh_timeout",
    default=0,
    show_default=True,
    type=int,
    help="Delay of server coordinates refreshing",
)
async def main(
    server,
    routes_number,
    buses_per_route,
    websockets_number,
    emulator_id,
    refresh_timeout,
):
    mem_channels = []
    for _ in range(websockets_number):
        mem_channels.append(trio.open_memory_channel(0))

    try:
        async with trio.open_nursery() as nursery:

            for bus in range(1, buses_per_route + 1):
                for route in itertools.islice(load_routes(), routes_number):

                    bus_id = generate_bus_id(emulator_id, route["name"], bus)

                    # Pick random channel for every bus
                    send_channel, receive_channel = random.choice(mem_channels)

                    try:
                        nursery.start_soon(run_bus, bus_id, route, send_channel)
                        nursery.start_soon(
                            send_updates, server, receive_channel
                        )
                    except ConnectionClosed:
                        break

    except OSError as ose:
        print("Connection attempt failed: %s" % ose, file=stderr)


main(_anyio_backend="trio")
