import argparse
import asyncio
import json
import logging
import os

from utils import connect, sanitize
from constants import SERVER_WRITE_PORT, SERVER_HOST, TOKEN


async def submit_message(reader, writer, message):
    message = '{}\n\n'.format(sanitize(message))
    writer.write(message.encode())
    logging.info('Sent message: {}'.format(sanitize(message)))

    data = await reader.readline()  # Message send. Write more
    logging.info('Received: {}'.format(data.decode()))


async def register(reader, writer, username):
    logging.info('Register: Try username {}'.format(username))

    writer.write('\n'.encode())
    await reader.readline()  # Enter preferred nickname below:

    message = '{}\n'.format(sanitize(username))
    writer.write(message.encode())

    data = await reader.readline()  # {"nickname": ... , "account_hash": ...}

    response = json.loads(data.decode())
    os.environ['TOKEN'] = response['account_hash']

    logging.info('Register: Username "{}" registered with token {}'.format(
        sanitize(username),
        os.environ['TOKEN']
    ))

    await reader.readline()  # Welcome to chat! Post your message below.


async def authorise(reader, writer, token):
    message = token + '\n'
    writer.write(message.encode())

    data = await reader.readline()  # {"nickname": ... , "account_hash": ...}

    response = json.loads(data.decode())
    if not response:
        logging.info("Invalid token: {}".format(token))
        print("Invalid token. Check it or register again")
        return False

    data = await reader.readline()  # Welcome to chat! Post your message below
    logging.info('Received: {}'.format(data.decode()))
    return True


async def dive_into_chatting(host, port, token, username, message):
    reader, writer = await connect((host, port))

    await reader.readline()  # 'Hello %username%!

    if token:
        token_is_valid = await authorise(reader, writer, token)
        if token_is_valid:
            # Override token in env to be able to send messages
            # without explicit token for next requests
            os.environ["TOKEN"] = token
            await submit_message(reader, writer, message)
    elif username:
        await register(reader, writer, username)
        await submit_message(reader, writer, message)

    logging.info('Close the connection')
    writer.close()


def get_arguments(host, port, token, username, message):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Host to connect')
    parser.add_argument('--port', type=str, help='Port to connect')
    parser.add_argument('--message', type=str, help='Message')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--token', type=str, help='Token')
    group.add_argument('--username', type=str, help='Username')

    args = parser.parse_args()
    if args.username:
        token = None
    if args.token:
        username = None

    parser.set_defaults(
        host=host,
        port=port,
        token=token,
        username=username,
        message=message
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
        os.getenv('SERVER_WRITE_PORT', SERVER_WRITE_PORT),
        os.getenv('TOKEN', TOKEN),
        os.getenv('USERNAME'),
        os.getenv('MESSAGE', 'Hello from Python')
    )

    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    loop.run_until_complete(dive_into_chatting(**args))
    loop.close()


if __name__ == '__main__':
    main()
