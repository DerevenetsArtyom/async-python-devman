from quart import websocket, render_template, request
from dotenv import load_dotenv
import os

from quart_trio import QuartTrio

from main import request_smsc

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
    load_dotenv()

    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    phone = os.getenv("PHONE")

    form = await request.form
    message = form["text"]
    res = await request_smsc('send', login, password, {"phones": phone}, message)
    print('res', res)
    return {}


@app.websocket('/ws')
async def ws():
    while True:
        await websocket.send('hello')


app.run('0.0.0.0', port=5000)
