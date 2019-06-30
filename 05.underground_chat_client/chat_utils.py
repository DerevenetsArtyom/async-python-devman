import asyncio
import json
import logging


class InvalidToken(Exception):
    pass


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


def sanitize(message):
    return message.replace('\n', '').replace('\r', '')


async def submit_message(reader, writer, message):
    message = '{}\n\n'.format(sanitize(message))
    writer.write(message.encode())
    await writer.drain()
    logging.info('submit_message: Sent message: {}'.format(sanitize(message)))

    data = await reader.readline()
    logging.info('submit_message: Received: {}'.format(data.decode()))


async def authorise(reader, writer, token):
    message = token + '\n'
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    response = json.loads(data.decode())
    if not response:
        logging.info("Invalid token: {}".format(token))
        return False, _

    data = await reader.readline()
    logging.info('authorise: Received: {}'.format(data.decode()))
    return True, response["nickname"]
