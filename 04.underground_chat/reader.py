import argparse
import asyncio
import datetime
import os
import logging

import aiofiles

from constants import SERVER_READ_PORT, SERVER_HOST, HISTORY

# python3 listen-minechat.py
#   --host 192.168.0.1
#   --port 5001
#   --history ~/minechat.history

# TODO: 3.Создайте защиту от обрыва соединения
# TODO: 4.Сохраните историю переписки в файл

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


async def tcp_client(host, port, history):
    while True:
        try:
            reader, writer = await connect((host, port))

            async with aiofiles.open(history, 'a') as file:
                while True:
                    data = await reader.readline()
                    await log_to_file(data.decode(), file)

        except Exception as e:
            print(e)
            continue


async def log_to_file(message, file):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y.%m.%d %H:%M")

    log = f'[{timestamp}] {message}'
    await file.write(log)
    logging.info(message)


def get_arguments(host, port, history):
    parser = argparse.ArgumentParser()
    # TODO: add help strings
    parser.add_argument('--host', type=str, help='')
    parser.add_argument('--port', type=str, help='')
    parser.add_argument('--history', type=str, help='')

    parser.set_defaults(
        host=host,
        port=port,
        history=history,
    )
    args = parser.parse_args()
    return vars(args)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    args = get_arguments(
        os.getenv('CHAT_HOST', SERVER_HOST),
        os.getenv('SERVER_READ_PORT', SERVER_READ_PORT),
        os.getenv('HISTORY', HISTORY),
    )

    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    loop.run_until_complete(tcp_client(**args))
    loop.close()


if __name__ == '__main__':
    main()
