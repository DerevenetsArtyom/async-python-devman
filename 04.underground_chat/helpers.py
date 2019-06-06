import asyncio
import datetime
import logging

import aiofiles


def sanitize(message):
    return message.replace('\n', '').replace('\r', '')


async def log_to_file(message, file):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y.%m.%d %H:%M")

    log = f'[{timestamp}] {message}'
    await file.write(log)
    logging.info(message)


async def connect(server, history=None):
    """Set up re-connection for client"""
    while True:
        try:
            reader, writer = await asyncio.open_connection(*server)
            if history:
                async with aiofiles.open(history, 'a') as file:
                    await log_to_file('Connection set up!\n', file)
            return reader, writer

        except (ConnectionRefusedError, ConnectionResetError) as e:
            logging.info(e)
            if history:
                async with aiofiles.open(history, 'a') as file:
                    await log_to_file(
                        "Connection error, retrying in 5 seconds...", file)
            logging.info("Connection error, retrying in 5 seconds...")

            await asyncio.sleep(5)
