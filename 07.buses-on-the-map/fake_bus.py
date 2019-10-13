import json

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed


message = {
    "busId": "156", "lat": None, "lng": None, "route": 156
}

with open("routes/156.json") as f:
    bus_info = json.loads(f.read())


async def main():
    try:
        async with open_websocket_url('ws://127.0.0.1:8080') as ws:
            while True:
                for coordinates in bus_info["coordinates"]:
                    try:
                        message["lat"] = coordinates[0]
                        message["lng"] = coordinates[1]

                        await ws.send_message(json.dumps(message))

                        await trio.sleep(0.5)
                    except ConnectionClosed:
                        break

    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


trio.run(main)


