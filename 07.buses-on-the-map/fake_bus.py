import os
import json

import trio
from sys import stderr
from trio_websocket import open_websocket_url, ConnectionClosed

message = {
    "busId": None, "lat": None, "lng": None, "route": None
}


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


# usage example
# for route in load_routes()[:10]:


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
