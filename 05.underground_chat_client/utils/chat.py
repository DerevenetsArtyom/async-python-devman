import asyncio
import json
import logging

from dotenv import set_key, find_dotenv


class InvalidTokenException(Exception):
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
        logging.info("authorise: Invalid token: {}".format(token))
        return False, None

    data = await reader.readline()
    logging.info('authorise: Received: {}'.format(data.decode()))
    return True, response["nickname"]


async def register(reader, writer, username):
    logging.info('Register: Try username {}'.format(username))

    writer.write('\n'.encode())
    await writer.drain()

    await reader.readline()

    message = '{}\n'.format(sanitize(username))
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    response = json.loads(data.decode())
    set_key(find_dotenv(), 'TOKEN', response['account_hash'])

    logging.info('Register: Username "{}" registered with token {}'.format(
        sanitize(username),
        response['account_hash']
    ))

    await reader.readline()
