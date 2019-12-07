import json
import random
import contextlib


import trio
from trio_websocket import open_websocket_url, ConnectionClosed


ERROR_MESSAGES = [
    json.dumps({"data": {'east_lng': 20, 'north_lat': 20, 'south_lat': 20, 'west_lng': 35}}),
    json.dumps({'msgType': 'Error Msg Type'}),
    json.dumps({'msgType': 'newBounds', "data": {'lat': 20, 'north_lat': 30}}),
]


async def main():
    url = 'ws://127.0.0.1:8000'
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

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(main)

