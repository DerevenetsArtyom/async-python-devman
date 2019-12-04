import os
import json
import functools

import trio
from trio_websocket import ConnectionClosed, HandshakeError


def load_routes(directory_path="routes"):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, "r", encoding="utf8") as file:
                yield json.load(file)


def generate_bus_id(emulator_id, route_id, bus_index):
    if emulator_id:
        return f"{emulator_id}-{route_id}-{bus_index}"
    return f"{route_id}-{bus_index}"


def relaunch_on_disconnect(async_function):
    # TODO: increase counter each next attempt (easy),
    #  but reset to 3 after success (not implemented)

    @functools.wraps(async_function)
    async def inner(*args, **kwargs):
        counter = 3
        while True:
            try:
                await async_function(*args, **kwargs)

            except (HandshakeError, ConnectionClosed) as e:
                # TODO: logging
                print("!!! relaunch_on_disconnect", type(e))
                await trio.sleep(counter)

    return inner
