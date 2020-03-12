from quart import websocket, render_template, request

from quart_trio import QuartTrio

app = QuartTrio(__name__, template_folder='frontend')


@app.route('/')
async def hello():
    context = {
        "date": "01.02.2000",
        "mailingId": "33",
        "SMSText": "SMSText",
        "percentFulfilled": "33",
        "percentFailed": "11",
    }
    return await render_template('index.html', mailing=context)


@app.route('/send/', methods=['POST'])
async def send():
    # data = await request.get_data()  # Full raw body
    # print('data', data)
    form = await request.form
    text = form["text"]
    print('text', text)
    return {}


@app.websocket('/ws')
async def ws():
    while True:
        await websocket.send('hello')


app.run('0.0.0.0', port=5000)
