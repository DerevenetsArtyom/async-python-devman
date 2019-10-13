import trio
from trio_websocket import serve_websocket, ConnectionClosed
import json

message = {
    "msgType": "Buses",
    "buses": [
        {"busId": "c790сс", "lat": None, "lng": None, "route": "120"},
    ]
}

with open("routes/156.json") as f:
    bus_info = json.loads(f.read())


async def echo_server(request):
    ws = await request.accept()
    while True:
        for coordinates in bus_info["coordinates"]:
            try:
                message["buses"][0]["lat"] = coordinates[0]
                message["buses"][0]["lng"] = coordinates[1]

                await ws.send_message(json.dumps(message))

                await trio.sleep(0.5)
            except ConnectionClosed:
                break


async def main():
    await serve_websocket(echo_server, '127.0.0.1', 8000, ssl_context=None)


trio.run(main)
