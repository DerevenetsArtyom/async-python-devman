import argparse
import asyncio
import datetime
import os

import aiofiles

SERVER_HOST = 'minechat.dvmn.org'
SERVER_READ_PORT = 5000


# https://www.google.com/search?q=asyncio+tcp+handle+reconnection&oq=asyncio+tcp+handle+reconnection++&aqs=chrome..69i57.23573j0j1&sourceid=chrome&ie=UTF-8
# https://www.reddit.com/r/learnpython/comments/4a64g4/chat_server_client_asyncio_reconnect_client_if/
# https://stackoverflow.com/questions/25998394/how-to-reconnect-a-socket-on-asyncio
# https://github.com/crossbario/autobahn-python/issues/295


async def connect(server):
    """Set up re-connection for client"""
    while True:
        try:
            reader, writer = await asyncio.open_connection(*server)
            return reader, writer
        except (ConnectionRefusedError, ConnectionResetError) as e:
            print(e)
            print("Server not up retrying in 5 seconds...")
            await asyncio.sleep(5)


async def tcp_client(server, history):
    while True:
        try:
            print('Before connection!')
            reader, writer = await connect(server)
            print('Connected!')

            async with aiofiles.open(history, 'a') as file:
                while True:
                    data = await reader.readline()
                    message = data.decode()

                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y.%m.%d %H:%M")
                    to_file = f'[{timestamp}] {message}'
                    print(f'[{timestamp}] Received: {message!r}')
                    await file.write(to_file)
        except Exception as e:
            print(e)
            continue


def main():
    parser = argparse.ArgumentParser()
    # TODO: add help strings
    parser.add_argument('--host', type=str, help='')
    parser.add_argument('--port', type=str, help='')
    parser.add_argument('--history', type=str, help='')
    args = parser.parse_args()

    host = args.host or os.getenv('CHAT_HOST', SERVER_HOST)
    port = args.port or os.getenv('CHAT_PORT', SERVER_READ_PORT)
    history = args.history or os.getenv('HISTORY', 'minechat-history.txt')
    server = (host, port)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_client(server, history))
    loop.close()


if __name__ == '__main__':
    main()
