import contextlib
import json
from dataclasses import dataclass
import asyncclick as click

import trio
from trio_websocket import serve_websocket, ConnectionClosed

buses = {}  # global variable to collect buses info -  {bus_id: bus_info}


@dataclass
class Bus:
    busId: str
    route: str
    lat: float
    lng: float


@dataclass
class WindowBounds:
    south_lat: float = 0.0
    north_lat: float = 0.0
    west_lng: float = 0.0
    east_lng: float = 0.0

    def is_inside(self, lat, lng):
        lat_inside = self.south_lat < lat < self.north_lat
        lng_inside = self.west_lng < lng < self.east_lng
        return lat_inside and lng_inside

    def update(self, south_lat, north_lat, west_lng, east_lng):
        print("update", south_lat, north_lat, west_lng, east_lng)
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


async def send_buses(ws, bounds):
    buses_inside = [
        bus_info
        for _, bus_info in buses.items()
        if bounds.is_inside(bus_info.lat, bus_info.lng)
    ]
    # TODO: logging (N buses inside bounds)

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

    msg = json.dumps(message_to_browser)
    print("send_buses:", msg)
    await ws.send_message(msg)


async def talk_to_browser(ws, bounds):
    """Send buses data to browser every second according to current bounds"""
    while True:
        try:
            await send_buses(ws, bounds)
        except ConnectionClosed:
            # TODO: logging
            print("talk_to_browser: ConnectionClosed")
            break

        await trio.sleep(1)


async def listen_browser(ws, bounds):
    """Receive a message with window bounds from browser and update it"""
    while True:
        try:
            json_message = await ws.get_message()
        except ConnectionClosed:
            # TODO: logging
            print("listen_browser: ConnectionClosed")
            break

        message = json.loads(json_message)
        # TODO: logging
        print("listen_browser:", message)

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
            # TODO: logging
            print("handle_simulator: ConnectionClosed")
            break

        message = json.loads(json_message)
        print("handle_simulator:", message)

        bus = Bus(**message)
        buses.update({bus.busId: bus})


@click.command()
@click.option(
    "--host", "-h",
    default="127.0.0.1",
    show_default=True,
    type=str,
    help="Server address",
)
@click.option(
    "--browser_port", "-bp",
    default=8000,
    type=int,
    show_default=True,
    help="Browser port. Send data to the browser through this port",
)
@click.option(
    "--simulator_port", "-sp",
    default=8080,
    show_default=True,
    type=int,
    help="Simulator port. Receive data from simulator through this port",
)
@click.option(
    "--verbose", '-v',
    is_flag=True,
    default=False,
    help="Enable logging",
    show_default=True
)
async def main(host, browser_port, simulator_port, verbose):
    simulator_address = (host, simulator_port)
    browser_address = (host, browser_port)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, handle_simulator, *simulator_address, None
        )
        nursery.start_soon(
            serve_websocket, handle_browser, *browser_address, None
        )


with contextlib.suppress(KeyboardInterrupt):
    main(_anyio_backend="trio")
