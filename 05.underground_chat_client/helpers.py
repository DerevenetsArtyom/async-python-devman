import asyncio
import datetime
import logging


async def connect(server):
    """Set up re-connection for client"""
    while True:
        try:
            reader, writer = await asyncio.open_connection(*server)
            return reader, writer

        except (ConnectionRefusedError, ConnectionResetError) as e:
            logging.info(e)
            logging.info("Connection error, retrying in 5 seconds...")

            await asyncio.sleep(5)


async def log_to_file(message, file):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y.%m.%d %H:%M")

    log = f'[{timestamp}] {message}'
    await file.write(log)
    logging.info(message)
