import json
import random
import contextlib


import trio
from trio_websocket import open_websocket_url, ConnectionClosed


ERROR_MESSAGES = [
    json.dumps({"busId": "c790ss", "lat": 55.7500}),
    json.dumps({"lng": 37.600, "route": "120"}),
    json.dumps({"busId": 333, "lat": 55.7500, "lng": 37.600, "route": "120"}),
    json.dumps({"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": 120}),
    json.dumps({"busId": "c790сс", "lat": [55.7500], "lng": [37.600], "route": "120"}),
]


async def main():
    url = 'ws://127.0.0.1:8080'
    async with open_websocket_url(url) as ws:
        while True:
            try:
                error_message = random.choice(ERROR_MESSAGES)
                await ws.send_message(error_message)
                print(f'Sent message "{error_message}" to {url}')
                message = await ws.get_message()
                print(f'Received message: {message}')
            except (OSError, ConnectionClosed) as e:
                print(f'Connection failed: {e}')
                break
            await trio.sleep(1)


with contextlib.suppress(KeyboardInterrupt):
    trio.run(main)
