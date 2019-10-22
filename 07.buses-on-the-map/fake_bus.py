import contextlib
import json
import itertools
import random
import asyncclick as click

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed
from utils import generate_bus_id, load_routes


# PRODUCER
async def run_bus(bus_id, route, send_channel):
    # Template for sending to the channel with updated values each time
    message = {"busId": None, "lat": None, "lng": None, "route": None}

    coordinates = route["coordinates"]
    start_offset = random.randrange(len(coordinates))

    # infinite loop to circle the route (start again after finish)
    while True:
        for coo in coordinates[start_offset:]:
            message["busId"] = bus_id
            message["route"] = route["name"]
            message["lat"] = coo[0]
            message["lng"] = coo[1]

            await send_channel.send(message)

        # Reset offset after first iteration to start from the beginning
        start_offset = 0


# CONSUMER
async def send_updates(server_address, receive_channel):
    # new function to gather and send data

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
    send_channels = []

    try:
        async with trio.open_nursery() as nursery:

            # Prepare memory channels: separate task for every 'receive_channel'
            # and collect 'send_channel's to be randomly selected afterwards
            for _ in range(websockets_number):
                send_channel, receive_channel = trio.open_memory_channel(0)
                send_channels.append(send_channel)

                nursery.start_soon(send_updates, server, receive_channel)

            for bus in range(1, buses_per_route + 1):
                for route in itertools.islice(load_routes(), routes_number):

                    bus_id = generate_bus_id(emulator_id, route["name"], bus)

                    # Pick random 'send' channel for every bus
                    send_channel = random.choice(send_channels)

                    try:
                        nursery.start_soon(run_bus, bus_id, route, send_channel)
                    except ConnectionClosed:
                        break

    except OSError as ose:
        print("Connection attempt failed: %s" % ose, file=stderr)


with contextlib.suppress(KeyboardInterrupt):
    main(_anyio_backend="trio")
