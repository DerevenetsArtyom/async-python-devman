import argparse
import asyncio
import datetime
import os
import logging

import aiofiles
from dotenv import load_dotenv

from constants import SERVER_READ_PORT, SERVER_HOST, HISTORY


async def connect(server, history):
    """Set up re-connection for client"""
    while True:
        try:
            reader, writer = await asyncio.open_connection(*server)
            async with aiofiles.open(history, 'a') as file:
                await log_to_file('Connection set up!', file)
            return reader, writer
        except (ConnectionRefusedError, ConnectionResetError) as e:
            logging.info(e)
            async with aiofiles.open(history, 'a') as file:
                await log_to_file(
                    "Connection error, retrying in 5 seconds...", file)
            logging.info("Connection error, retrying in 5 seconds...")
            await asyncio.sleep(5)


async def tcp_client(host, port, history):
    while True:
        try:
            reader, writer = await connect((host, port), history)

            async with aiofiles.open(history, 'a') as file:
                while True:
                    data = await reader.readline()
                    await log_to_file(data.decode(), file)

        except Exception as e:
            logging.info(e)
            continue


async def log_to_file(message, file):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y.%m.%d %H:%M")

    log = f'[{timestamp}] {message}'
    await file.write(log)
    logging.info(message)


def get_arguments(host, port, history):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Host to connect')
    parser.add_argument('--port', type=str, help='Port to connect')
    parser.add_argument('--history', type=str, help='Path to history file')

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
    load_dotenv()
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
