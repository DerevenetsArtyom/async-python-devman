import argparse
import asyncio
import logging
import os
import socket
from contextlib import asynccontextmanager

import aionursery
from async_timeout import timeout
from dotenv import load_dotenv

import gui
from loggers import setup_logger
from utils.chat import submit_message, register, authorise
from utils.files import load_from_log_file, save_messages_to_file
from utils.general import create_handy_nursery

WATCH_CONNECTION_TIMEOUT = 20
PING_PONG_TIMEOUT = 30
DELAY_BETWEEN_PING_PONG = 5

main_logger = logging.getLogger('main_logger')
watchdog_logger = logging.getLogger('watchdog_logger')


@asynccontextmanager
async def get_connection(host, port, status_updates_queue, state):
    reader, writer = await asyncio.open_connection(host, port)
    try:
        yield (reader, writer)
    finally:
        status_updates_queue.put_nowait(state.CLOSED)
        writer.close()


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


async def send_messages(sending_queue, status_updates_queue,
                        watchdog_queue, reader, writer):
    """
    Listen 'sending_queue' and submit messages when present.
    Assume that authentication / registration was done before executing that.
    """
    status_updates_queue.put_nowait(
        gui.SendingConnectionStateChanged.ESTABLISHED)

    while True:
        message = await sending_queue.get()
        await submit_message(reader, writer, message)
        watchdog_queue.put_nowait('Connection is alive. Message sent')


async def read_messages(host, read_port, history, messages_queue, logging_queue,
                        status_updates_queue, watchdog_queue):
    """
    Read messages from the remote server and put it
    in 'messages_queue' to be displayed in GUI afterwards.
    Also put messages in 'logging_queue' to save it to log file.
    If there is any messages already in the log file - display it first in GUI.
    """
    read_connection_state = gui.ReadConnectionStateChanged

    messages_queue.put_nowait('** LOADING MESSAGE HISTORY.... **')
    await load_from_log_file(history, messages_queue)
    messages_queue.put_nowait('** HISTORY IS SHOWN ABOVE **\n')

    status_updates_queue.put_nowait(read_connection_state.INITIATED)

    async with get_connection(host, read_port, status_updates_queue,
                              read_connection_state) as (reader, _):
        status_updates_queue.put_nowait(read_connection_state.ESTABLISHED)

        while True:
            data = await reader.readline()
            message = data.decode()
            messages_queue.put_nowait(message.strip())
            logging_queue.put_nowait(message)
            watchdog_queue.put_nowait('Connection is alive.New message in chat')


async def watch_for_connection(watchdog_queue):
    """Timer to monitor network connection by checking time between packages"""
    while True:
        try:
            async with timeout(WATCH_CONNECTION_TIMEOUT):
                message = await watchdog_queue.get()
                watchdog_logger.info(message)
        except asyncio.TimeoutError:
            watchdog_logger.info(f'{WATCH_CONNECTION_TIMEOUT}s is elapsed')
            raise ConnectionError()


async def handle_connection(host, read_port, write_port, history, token,
                            messages_queue, sending_queue, status_updates_queue,
                            logging_queue, watchdog_queue):
    send_connection_state = gui.SendingConnectionStateChanged

    while True:

        async with get_connection(
                host, write_port, status_updates_queue,
                send_connection_state) as (reader, writer):

            status_updates_queue.put_nowait(send_connection_state.INITIATED)

            watchdog_queue.put_nowait('Connection is alive. Prompt before auth')

            await reader.readline()
            token_is_valid, username = await authorise(reader, writer, token)
            if token_is_valid:
                # Override token in env to be able to send messages
                # without explicit token for next requests
                os.environ["TOKEN"] = token

                watchdog_queue.put_nowait('Connection is alive. Authorization done')

            else:
                username = gui.msg_box(
                    'Invalid token',
                    'If you\'re registered user, please'
                    ' click "Cancel" and check your .env file.\n If you\'re'
                    ' the new one, enter yor name below and click "OK"')

                if username is None:
                    print("raise UserInterrupt('User Interrupt')")

                await register(reader, writer, username)

            # Show received username in GUI
            status_updates_queue.put_nowait(gui.NicknameReceived(username))

            async with create_handy_nursery() as nursery:
                nursery.start_soon(
                    read_messages(
                        host, read_port, history, messages_queue,
                        logging_queue, status_updates_queue, watchdog_queue
                    )
                )

                nursery.start_soon(
                    send_messages(
                        sending_queue, status_updates_queue,
                        watchdog_queue, reader, writer
                    )
                )

                nursery.start_soon(watch_for_connection(watchdog_queue))
                nursery.start_soon(ping_pong(reader, writer, watchdog_queue))

            # break the infinite loop to make possible to catch exeptions
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
    # TODO: nothing going to appear in that logger: setup_logger('main_logger')
    setup_logger(
        'watchdog_logger', fmt='[%(asctime)s] %(message)s', datefmt='%s'
    )
    setup_logger('')

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
    status_updates_queue = asyncio.Queue()

    logging_queue = asyncio.Queue()  # use to write incoming messages to file
    watchdog_queue = asyncio.Queue()  # use to track server connection

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(
                gui.draw(messages_queue, sending_queue, status_updates_queue)
            )

            nursery.start_soon(
                handle_connection(
                    host, read_port, write_port, history, token,
                    messages_queue, sending_queue, status_updates_queue,
                    logging_queue, watchdog_queue,
                )
            )

            nursery.start_soon(save_messages_to_file(history, logging_queue))

    except aionursery.MultiError as e:
        # TODO: that doesn't catch the exception.'read_messages' hangs
        print('#### aionursery.MultiError')
        print(e.exceptions)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed):
        print('******************** KeyboardInterrupt, gui.TkAppClosed')
        exit()
