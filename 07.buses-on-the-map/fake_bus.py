import contextlib
import json
import itertools
import logging
import random
import asyncclick as click
import functools

import trio
from trio_websocket import open_websocket_url, ConnectionClosed, HandshakeError
from utils import generate_bus_id, load_routes


def relaunch_on_disconnect(async_function):
    # TODO: increase counter each next attempt (easy),
    #  but reset to 3 after success (not implemented)

    @functools.wraps(async_function)
    async def inner(*args, **kwargs):
        counter = 3
        while True:
            try:
                await async_function(*args, **kwargs)

            except (HandshakeError, ConnectionClosed):
                logger.debug("Relaunch on disconnect")
                await trio.sleep(counter)

    return inner


async def run_bus(bus_id, route, send_channel):
    # Template message to send to the channel with updated values each time
    message = {"busId": None, "lat": None, "lng": None, "route": None}

    coordinates = route["coordinates"]

    # set starting point for different bus
    # with different coordinates om the same route
    start_offset = random.randrange(len(coordinates))

    # infinite loop to circle the route (start again after finish)
    while True:
        for latitude, longitude in coordinates[start_offset:]:
            message.update(
                {
                    "busId": bus_id,
                    "route": route["name"],
                    "lat": latitude,
                    "lng": longitude,
                }
            )

            await send_channel.send(message)

        # Reset offset after first iteration to start route from the beginning
        start_offset = 0


@relaunch_on_disconnect
async def send_updates(server_address, receive_channel, refresh_timeout):
    async with open_websocket_url(server_address) as ws:
        async for value in receive_channel:
            await ws.send_message(json.dumps(value, ensure_ascii=True))
            # without that delay buses go crazy on the map
            await trio.sleep(refresh_timeout)


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
    help="Amount of routes. There are 963 routes available",
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
    default=0.1,
    show_default=True,
    type=float,
    help="Delay of server coordinates refreshing",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable logging",
    show_default=True,
)
async def main(
    server,
    routes_number,
    buses_per_route,
    websockets_number,
    emulator_id,
    refresh_timeout,
    verbose,
):
    if not verbose:
        app_logger = logging.getLogger("app_logger")
        app_logger.disabled = True

    send_channels = []
    try:
        async with trio.open_nursery() as nursery:

            # Prepare memory channels: separate task for every 'receive_channel'
            # and accumulate 'send_channel's to be randomly selected afterwards
            for _ in range(websockets_number):
                send_channel, receive_channel = trio.open_memory_channel(0)
                send_channels.append(send_channel)

                nursery.start_soon(
                    send_updates, server, receive_channel, refresh_timeout
                )

            for bus_number in range(1, buses_per_route + 1):
                for route in itertools.islice(load_routes(), routes_number):
                    bus_id = generate_bus_id(
                        emulator_id, route["name"], bus_number
                    )

                    # Pick random 'send' channel for every bus
                    send_channel = random.choice(send_channels)

                    try:
                        nursery.start_soon(run_bus, bus_id, route, send_channel)
                    except ConnectionClosed:
                        break

    except OSError as ose:
        logger.debug("Connection attempt failed: %s", ose)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        logger = logging.getLogger("app_logger")
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        main(_anyio_backend="trio")
