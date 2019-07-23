import argparse
import asyncio
import logging
import os
import socket
from tkinter import messagebox

import aionursery
from async_timeout import timeout
from dotenv import load_dotenv

import gui
from loggers import setup_logger
from utils.chat import (submit_message, register,
                        authorise, get_connection, UserInterrupt)
from utils.files import load_from_log_file, save_messages_to_file
from utils.general import create_handy_nursery

WATCH_CONNECTION_TIMEOUT = 5
PING_PONG_TIMEOUT = 30
DELAY_BETWEEN_PING_PONG = 5

main_logger = logging.getLogger('main_logger')
watchdog_logger = logging.getLogger('watchdog_logger')


async def ping_pong(reader, writer, watchdog_queue):
    while True:
        try:
            async with timeout(PING_PONG_TIMEOUT):
                writer.write('\n'.encode())
                await writer.drain()

                await reader.readline()
            await asyncio.sleep(DELAY_BETWEEN_PING_PONG)
            watchdog_queue.put_nowait('Connection is alive. Ping message sent')

        except socket.gaierror:
            watchdog_queue.put_nowait('socket.gaierror')
            raise ConnectionError('socket.gaierror (no internet connection)')


async def send_messages(reader, writer, queues):
    """
    Listen 'sending_queue' and submit messages when present.
    Assume that authentication / registration was done before executing that.
    """
    queues['statuses'].put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

    while True:
        message = await queues['sending'].get()
        await submit_message(reader, writer, message)
        queues['watchdog'].put_nowait('Connection is alive. Message sent')


async def read_messages(host, read_port, history, queues):
    """
    Read messages from the remote server and put it into 'queues['messages']'
    to be displayed in GUI afterwards.
    Also put messages into 'logging_queue' to save it to the log file.
    If there are any messages already in the log file - display it first in GUI.
    """

    queues['messages'].put_nowait('** LOADING MESSAGE HISTORY.... **')
    await load_from_log_file(history, queues['messages'])
    queues['messages'].put_nowait('** HISTORY IS SHOWN ABOVE **\n')

    queues['statuses'].put_nowait(gui.ReadConnectionStateChanged.INITIATED)

    async with get_connection(host, read_port, queues['statuses'],
                              gui.ReadConnectionStateChanged) as (reader, _):
        queues['statuses'].put_nowait(
            gui.ReadConnectionStateChanged.ESTABLISHED)

        while True:
            data = await reader.readline()
            message = data.decode()
            queues['messages'].put_nowait(message.strip())
            queues['logging'].put_nowait(message)
            queues['watchdog'].put_nowait(
                'Connection is alive. New message in chat')


async def watch_for_connection(watchdog_queue):
    """ Timer to monitor network connection by checking time between packages"""
    while True:
        try:
            async with timeout(WATCH_CONNECTION_TIMEOUT):
                message = await watchdog_queue.get()
                watchdog_logger.info(message)
        except asyncio.TimeoutError:
            watchdog_logger.info(f'{WATCH_CONNECTION_TIMEOUT}s is elapsed')
            raise ConnectionError()


async def handle_connection(host, ports, history, token, queues):
    read_port, write_port = ports
    while True:
        async with get_connection(
                host, write_port, queues['statuses'],
                gui.ReadConnectionStateChanged) as (reader, writer):

            queues['statuses'].put_nowait(
                gui.ReadConnectionStateChanged.INITIATED)

            await reader.readline()
            queues['watchdog'].put_nowait(
                'Connection is alive. Prompt before auth')

            token_is_valid, username = await authorise(reader, writer, token)
            if token_is_valid:
                # Override token in env to be able to send messages
                # without explicit token for next requests
                os.environ["TOKEN"] = token

                queues['watchdog'].put_nowait(
                    'Connection is alive. Authorization done')

            else:
                username = gui.msg_box(
                    'Invalid token',
                    'If you\'re registered user, please '
                    'click "Cancel" and check your .env file.\n If you\'re '
                    'the new one, enter yor name below and click "OK"')

                if username == "":
                    main_logger.info("User left 'username' empty")

                    messagebox.showinfo(
                        "Invalid username",
                        "You entered empty 'username'. This is not allowed."
                        "Program is going to terminate."
                    )
                    raise UserInterrupt()

                if username is None:
                    main_logger.info("User canceled 'username' input")
                    raise UserInterrupt()

                await register(reader, writer, username)

            # Show received username in GUI
            queues['statuses'].put_nowait(gui.NicknameReceived(username))

            async with create_handy_nursery() as nursery:
                nursery.start_soon(
                    read_messages(host, read_port, history, queues)
                )

                nursery.start_soon(send_messages(reader, writer, queues))

                nursery.start_soon(watch_for_connection(queues['watchdog']))

                nursery.start_soon(
                    ping_pong(reader, writer, queues['watchdog'])
                )

            # break the infinite loop to make possible to catch exceptions
            return


def get_arguments(host, read_port, write_port, token, history):
    parser = argparse.ArgumentParser()
    add_argument = parser.add_argument

    add_argument('--host', type=str, help='Host to connect')
    add_argument('--read-port', type=str, help='Port to connect for reading')
    add_argument('--write-port', type=str, help='Port to connect for writing')
    add_argument('--token', type=str, help='Token')
    add_argument('--history', type=str, help='Path to history file')

    parser.set_defaults(
        host=host,
        read_port=read_port,
        write_port=write_port,
        token=token,
        history=history,
    )
    args_namespace = parser.parse_args()
    args = vars(args_namespace)
    return (args['host'], args['read_port'],
            args['write_port'], args['token'], args['history'])


async def main():
    setup_logger('main_logger')
    setup_logger(
        'watchdog_logger', fmt='[%(asctime)s] %(message)s', datefmt='%s'
    )

    load_dotenv()
    host, read_port, write_port, token, history = get_arguments(
        os.getenv('MINECHAT_SERVER_HOST'),
        os.getenv('MINECHAT_SERVER_READ_PORT'),
        os.getenv('MINECHAT_SERVER_WRITE_PORT'),
        os.getenv('MINECHAT_TOKEN'),
        os.getenv('MINECHAT_HISTORY'),
    )

    # Queues must be created inside the loop.
    # If create them outside the loop created for asyncio.run(),
    # so they use events.get_event_loop().
    # asyncio.run() creates a new loop, and futures created for the queue
    # in one loop can't then be used in the other.
    queues = dict()
    queues['messages'] = asyncio.Queue()
    queues['sending'] = asyncio.Queue()
    queues['statuses'] = asyncio.Queue()

    queues['logging'] = asyncio.Queue()  # write incoming messages to file
    queues['watchdog'] = asyncio.Queue()  # track server connection

    ports = (read_port, write_port)
    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(
                gui.draw(
                    queues['messages'], queues['sending'], queues['statuses']
                )
            )

            nursery.start_soon(
                handle_connection(host, ports, history, token, queues)
            )

            nursery.start_soon(
                save_messages_to_file(history, queues['logging'])
            )

    except aionursery.MultiError as e:
        print('#### aionursery.MultiError')
        print(e.exceptions)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, ConnectionError, gui.TkAppClosed, UserInterrupt):
        exit()
