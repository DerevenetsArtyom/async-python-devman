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


# TODO: add all queues to single dict

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


async def send_messages(sending_queue, statuses_queue,
                        watchdog_queue, reader, writer):
    """
    Listen 'sending_queue' and submit messages when present.
    Assume that authentication / registration was done before executing that.
    """
    statuses_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

    while True:
        message = await sending_queue.get()
        await submit_message(reader, writer, message)
        watchdog_queue.put_nowait('Connection is alive. Message sent')


async def read_messages(host, read_port, history, messages_queue,
                        logging_queue, statuses_queue, watchdog_queue):
    """
    Read messages from the remote server and put it into 'messages_queue'
    to be displayed in GUI afterwards.
    Also put messages into 'logging_queue' to save it to the log file.
    If there are any messages already in the log file - display it first in GUI.
    """

    messages_queue.put_nowait('** LOADING MESSAGE HISTORY.... **')
    await load_from_log_file(history, messages_queue)
    messages_queue.put_nowait('** HISTORY IS SHOWN ABOVE **\n')

    statuses_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)

    async with get_connection(host, read_port, statuses_queue,
                              gui.ReadConnectionStateChanged) as (reader, _):
        statuses_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

        while True:
            data = await reader.readline()
            message = data.decode()
            messages_queue.put_nowait(message.strip())
            logging_queue.put_nowait(message)
            watchdog_queue.put_nowait(
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


async def handle_connection(host, read_port, write_port, history, token,
                            messages_queue, sending_queue, statuses_queue,
                            logging_queue, watchdog_queue):
    while True:
        async with get_connection(
                host, write_port, statuses_queue,
                gui.ReadConnectionStateChanged) as (reader, writer):

            statuses_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)

            await reader.readline()
            watchdog_queue.put_nowait('Connection is alive. Prompt before auth')

            token_is_valid, username = await authorise(reader, writer, token)
            if token_is_valid:
                # Override token in env to be able to send messages
                # without explicit token for next requests
                os.environ["TOKEN"] = token

                watchdog_queue.put_nowait(
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
            statuses_queue.put_nowait(gui.NicknameReceived(username))

            async with create_handy_nursery() as nursery:
                nursery.start_soon(
                    read_messages(
                        host, read_port, history, messages_queue,
                        logging_queue, statuses_queue, watchdog_queue
                    )
                )

                nursery.start_soon(
                    send_messages(
                        sending_queue, statuses_queue,
                        watchdog_queue, reader, writer
                    )
                )

                nursery.start_soon(watch_for_connection(watchdog_queue))

                nursery.start_soon(ping_pong(reader, writer, watchdog_queue))

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
        os.getenv('SERVER_HOST'),
        os.getenv('SERVER_READ_PORT'),
        os.getenv('SERVER_WRITE_PORT'),
        os.getenv('TOKEN'),
        os.getenv('HISTORY'),
        # os.getenv('USERNAME'),
    )

    # Queues must be created inside the loop.
    # If create them outside the loop created for asyncio.run(),
    # so they use events.get_event_loop().
    # asyncio.run() creates a new loop, and futures created for the queue
    # in one loop can't then be used in the other.
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    statuses_queue = asyncio.Queue()

    logging_queue = asyncio.Queue()  # use to write incoming messages to file
    watchdog_queue = asyncio.Queue()  # use to track server connection

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(
                gui.draw(messages_queue, sending_queue, statuses_queue)
            )

            nursery.start_soon(
                handle_connection(
                    host, read_port, write_port, history, token,
                    messages_queue, sending_queue, statuses_queue,
                    logging_queue, watchdog_queue,
                )
            )

            nursery.start_soon(save_messages_to_file(history, logging_queue))

    except aionursery.MultiError as e:
        print('#### aionursery.MultiError')
        print(e.exceptions)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, ConnectionError, gui.TkAppClosed, UserInterrupt):
        print('******************** KeyboardInterrupt, gui.TkAppClosed')
        exit()
