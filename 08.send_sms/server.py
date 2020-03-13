import trio
from quart import websocket, render_template, request
from dotenv import load_dotenv
import json
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
    message = {
        "msgType": "SMSMailingStatus",
        "SMSMailings": [
            {
                "timestamp": 1123131392.734,
                "SMSText": "Сегодня гроза! Будьте осторожны!",
                "mailingId": "1",
                "totalSMSAmount": 100,
                "deliveredSMSAmount": 0,
                "failedSMSAmount": 5,
            }
        ]
    }

    while True:
        for i in range(100):
            message["SMSMailings"][0]["deliveredSMSAmount"] = i
            await websocket.send(json.dumps(message))
            await trio.sleep(1)


app.run('0.0.0.0', port=5000)
