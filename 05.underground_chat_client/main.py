import argparse
import asyncio
import contextlib
import logging
import os
from tkinter import messagebox

import aionursery
from async_timeout import timeout
from dotenv import load_dotenv

import gui
from chat_utils import submit_message, authorise, connect, InvalidToken
from files_utils import load_from_log_file, save_messages_to_file
from gui import (ReadConnectionStateChanged, NicknameReceived,
                 SendingConnectionStateChanged)
from loggers import setup_logger

main_logger = logging.getLogger('main_logger')
watchdog_logger = logging.getLogger('watchdog_logger')


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        raise


async def send_messages(host, write_port, token, sending_queue,
                        status_updates_queue, watchdog_queue):
    status_updates_queue.put_nowait(SendingConnectionStateChanged.INITIATED)

    reader, writer = await connect((host, write_port))
    status_updates_queue.put_nowait(
        SendingConnectionStateChanged.ESTABLISHED
    )

    while True:
        try:
            await reader.readline()
            watchdog_queue.put_nowait('Connection is alive. Prompt before auth')

            token_is_valid, username = await authorise(reader, writer, token)
            if token_is_valid:
                # Override token in env to be able to send messages
                # without explicit token for next requests
                os.environ["TOKEN"] = token

                # Show received username in GUI
                status_updates_queue.put_nowait(NicknameReceived(username))

                watchdog_queue.put_nowait(
                    'Connection is alive. Authorization done')

                message = await sending_queue.get()
                await submit_message(reader, writer, message)
                watchdog_queue.put_nowait('Connection is alive. Message sent')

            else:
                messagebox.showerror(
                    "Invalid token",
                    "Check the token, server couldn't recognize it"
                )
                raise InvalidToken()

        finally:
            status_updates_queue.put_nowait(
                SendingConnectionStateChanged.CLOSED
            )
            writer.close()


async def read_messages(host, port, history, messages_queue, logging_queue,
                        status_updates_queue, watchdog_queue):
    """
    Read messages from the remote server and put it
    in 'messages_queue' to be displayed in GUI afterwards.
    Also put messages in 'logging_queue' to save it to log file.
    If there is any messages already in the log file - display it first in GUI.
    """
    watchdog_message = 'Connection is alive. New message in chat'

    await load_from_log_file(history, messages_queue)

    status_updates_queue.put_nowait(ReadConnectionStateChanged.INITIATED)

    while True:
        reader, writer = await connect((host, port))
        status_updates_queue.put_nowait(ReadConnectionStateChanged.ESTABLISHED)
        try:
            while True:
                data = await reader.readline()
                message = data.decode()
                messages_queue.put_nowait(message.strip())
                logging_queue.put_nowait(message)
                watchdog_queue.put_nowait(watchdog_message)

        except Exception as e:
            print(e)
            continue
        finally:
            status_updates_queue.put_nowait(ReadConnectionStateChanged.CLOSED)
            writer.close()


async def watch_for_connection(watchdog_queue):
    """Timer to monitor network connection by checking time between packages"""
    # TODO: raise ConnectionError внутри watch_for_connection
    while True:
        try:
            async with timeout(2):
                message = await watchdog_queue.get()
                watchdog_logger.info(message)
        except asyncio.TimeoutError:
            watchdog_logger.info('2s timeout is elapsed')
            raise ConnectionError


async def start(host, read_port, write_port, token, history):
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
                    host, read_port, write_port, history, token, messages_queue,
                    sending_queue, status_updates_queue,
                    logging_queue, watchdog_queue,
                )
            )
    except InvalidToken:
        # TODO: #11: this actually doesn't work, program doesn't stop gracefully
        print('InvalidToken')
        return


# TODO декоратор reconnect, если у вас такой есть в старом коде
async def handle_connection(host, read_port, write_port, history, token,
                            messages_queue, sending_queue, status_updates_queue,
                            logging_queue, watchdog_queue):
    # TODO:
    #  * infinite 'while True'

    async with create_handy_nursery() as nursery:
        # while True:
        try:
            nursery.start_soon(read_messages(
                host, read_port, history, messages_queue, logging_queue,
                status_updates_queue, watchdog_queue
            ))

            nursery.start_soon(send_messages(
                host, write_port, token, sending_queue,
                status_updates_queue, watchdog_queue
            ))

            nursery.start_soon(save_messages_to_file(history, logging_queue))

            nursery.start_soon(watch_for_connection(watchdog_queue))
        except aionursery.MultiError as e:
            # TODO: that doesn't catch the exception.'read_messages' hangs
            print('aionursery.MultiError')
            print(e.exceptions)
        except Exception as e:
            print('Exception', e)


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
    args = parser.parse_args()
    return vars(args)


def main():
    # TODO: check 'Схема запуска корутин' in step #15, could be wrong setup

    # TODO: nothing going to appear in that logger: setup_logger('main_logger')
    setup_logger('watchdog_logger',
                 fmt='[%(asctime)s] %(message)s', datefmt='%s')

    load_dotenv()
    args = get_arguments(
        os.getenv('SERVER_HOST'),
        os.getenv('SERVER_READ_PORT'),
        os.getenv('SERVER_WRITE_PORT'),
        os.getenv('TOKEN'),
        os.getenv('HISTORY'),
        # os.getenv('USERNAME'),
    )

    # TODO: #10: add graceful shutdown: KeyboardInterrupt, gui.TkAppClosed
    asyncio.run(start(**args), debug=True)


if __name__ == '__main__':
    main()
