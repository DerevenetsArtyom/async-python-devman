import asyncio
import json
import logging
from contextlib import asynccontextmanager

from dotenv import set_key, find_dotenv

main_logger = logging.getLogger('main_logger')


class UserInterrupt(Exception):
    pass


@asynccontextmanager
async def get_connection(host, port, status_updates_queue, state):
    reader, writer = await asyncio.open_connection(host, port)
    try:
        yield (reader, writer)
    finally:
        status_updates_queue.put_nowait(state.CLOSED)
        writer.close()


def sanitize(message):
    return message.replace('\n', '').replace('\r', '')


async def submit_message(reader, writer, message):
    message = '{}\n\n'.format(sanitize(message))
    writer.write(message.encode())
    await writer.drain()
    main_logger.info('submit_message: Sent message: {}'.format(message.strip()))

    data = await reader.readline()
    text = data.decode().strip()
    main_logger.info('submit_message: Received: {}'.format(text))


async def authorise(reader, writer, token):
    message = token + '\n'
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    response = json.loads(data.decode())
    if not response:
        main_logger.info('authorise: Invalid token: {}'.format(token))
        return False, None

    data = await reader.readline()
    main_logger.info('authorise: Received: {}'.format(data.decode()))
    return True, response["nickname"]


async def register(reader, writer, username):
    main_logger.info('register: Try username {}'.format(username))

    writer.write('\n'.encode())
    await writer.drain()

    await reader.readline()

    message = '{}\n'.format(sanitize(username))
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    response = json.loads(data.decode())
    set_key(find_dotenv(), 'TOKEN', response['account_hash'])

    main_logger.info('register: Username "{}" registered with token {}'.format(
        sanitize(username),
        response['account_hash']
    ))

    await reader.readline()
