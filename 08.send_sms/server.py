from quart import websocket

from quart_trio import QuartTrio

app = QuartTrio(__name__)


@app.route('/')
async def hello():
    return 'hello there'


@app.websocket('/ws')
async def ws():
    while True:
        await websocket.send('hello')


app.run('0.0.0.0', port=5000)
