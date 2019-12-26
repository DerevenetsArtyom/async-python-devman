import contextlib
import json
import logging
import asyncclick as click

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from models import WindowBounds, Bus, MessageSource
from utils import (
    validate_bus_message,
    validate_client_message,
    validate_message,
)

logger = logging.getLogger("app_logger")

buses = {}  # global variable to collect buses info -  {bus_id: bus_info}


async def send_buses(ws, bounds):
    buses_inside = [
        bus_info
        for _, bus_info in buses.items()
        if bounds.is_inside(bus_info.lat, bus_info.lng)
    ]

    if bounds.errors:
        message_to_browser = {"msgType": "Errors", "errors": bounds.errors}
    else:
        message_to_browser = {
            "msgType": "Buses",
            "buses": [
                {
                    "busId": bus.busId,
                    "lat": bus.lat,
                    "lng": bus.lng,
                    "route": bus.busId,
                }
                for bus in buses_inside
            ],
        }

    logger.debug("send_buses: inside bounds %s buses", len(buses_inside))
    msg = json.dumps(message_to_browser)
    await ws.send_message(msg)


async def talk_to_browser(ws, bounds):
    """Periodically send buses data to browser according to current bounds"""
    while True:
        try:
            await send_buses(ws, bounds)
        except ConnectionClosed:
            logger.debug("*** talk_to_browser: ConnectionClosed ***")
            break

        await trio.sleep(0.1)


async def listen_browser(ws, bounds):
    """Receive a message with window bounds from browser and update it"""
    while True:
        try:
            json_message = await ws.get_message()
        except ConnectionClosed:
            logger.debug("*** listen_browser: ConnectionClosed ***")
            break

        logger.debug("listen_browser: %s", json_message)

        message = validate_message(json_message, MessageSource.browser)
        errors = message.get("errors")

        if errors:
            bounds.register_errors(errors)
        else:
            bounds.update(**message["data"])


async def handle_browser(request):
    """Responsible for communication with browser: send and receive data"""
    bounds = WindowBounds()
    ws = await request.accept()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(talk_to_browser, ws, bounds)


async def handle_simulator(request):
    """Receive data from simulator and update it in 'buses' for each bus"""
    ws = await request.accept()

    while True:
        try:
            json_message = await ws.get_message()
        except ConnectionClosed:
            logger.debug("*** handle_simulator: ConnectionClosed ***")
            break

        message = validate_message(json_message, MessageSource.bus)
        errors = message.get("errors")

        logger.debug("handle_simulator: %s", message)
        if errors:
            error_message = json.dumps({"msgType": "Errors", "errors": errors})
            await ws.send_message(error_message)
        else:
            bus = Bus(**message["data"])
            buses.update({bus.busId: bus})


@click.command()
@click.option(
    "--host",
    "-h",
    default="127.0.0.1",
    show_default=True,
    type=str,
    help="Server address",
)
@click.option(
    "--browser_port",
    "-bp",
    default=8000,
    type=int,
    show_default=True,
    help="Send data to the browser through this port",
)
@click.option(
    "--simulator_port",
    "-sp",
    default=8080,
    show_default=True,
    type=int,
    help="Receive data from simulator through this port",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable logging",
    show_default=True,
)
async def main(host, browser_port, simulator_port, verbose):
    simulator_address = (host, simulator_port)
    browser_address = (host, browser_port)

    if not verbose:
        logger.disabled = True

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, handle_simulator, *simulator_address, None
        )
        nursery.start_soon(
            serve_websocket, handle_browser, *browser_address, None
        )


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)

        main(_anyio_backend="trio")
