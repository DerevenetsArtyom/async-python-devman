import contextlib
import json
from dataclasses import dataclass

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
        print('update', south_lat, north_lat, west_lng, east_lng)
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


async def send_buses(ws, bounds):
    # TODO: add here buses filtering by bounds
    message_to_browser = dict(msgType="Buses", buses=[])

    message_to_browser["buses"] = list(buses.values())
    msg = json.dumps(message_to_browser)

    # inside = []
    # for bus_id, bus_info in buses.items():
    #     if is_inside(bounds, bus_info["lat"], bus_info["lng"]):
    #         inside.append({bus_id: bus_info})
    #         print('inside', len(inside))

    print("send_buses:", msg)
    await ws.send_message(msg)


async def talk_to_browser(ws, bounds):
    """Send buses data to browser every second according to current bounds"""

    while True:
        try:
            await send_buses(ws, bounds)
        except ConnectionClosed:
            print("talk_to_browser: ConnectionClosed")
            break

        await trio.sleep(1)


def is_inside(bounds, lat, lng):
    if bounds['south_lat'] < lat < bounds['north_lat']:
        if bounds['west_lng'] < lng < bounds['east_lng']:
            return True
    return False


async def listen_browser(ws, bounds):
    """Receive a message with window bounds from browser and update it"""

    while True:
        try:
            json_message = await ws.get_message()
        except ConnectionClosed:
            print("listen_browser: ConnectionClosed")
            break

        message = json.loads(json_message)
        print("listen_browser:", message)

        bounds.update(**message['data'])


async def handle_browser(request):
    """Responsible for communication with browser: sena and receive data"""

    bounds = WindowBounds()
    ws = await request.accept()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(talk_to_browser, ws, bounds)


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

    simulator_address = (simulator_host, simulator_port)
    browser_address = (browser_host, browser_port)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket, handle_simulator, *simulator_address, None
        )
        nursery.start_soon(
            serve_websocket, handle_browser, *browser_address, None
        )


with contextlib.suppress(KeyboardInterrupt):
    trio.run(main)
