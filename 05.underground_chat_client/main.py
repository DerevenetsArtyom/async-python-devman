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
from utils.chat import submit_message, authorise, connect, InvalidTokenException
from utils.files import load_from_log_file, save_messages_to_file
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
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)

    reader, writer = await connect((host, write_port))
    status_updates_queue.put_nowait(
        gui.SendingConnectionStateChanged.ESTABLISHED
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
                status_updates_queue.put_nowait(gui.NicknameReceived(username))

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
                raise InvalidTokenException()

        finally:
            status_updates_queue.put_nowait(
                gui.SendingConnectionStateChanged.CLOSED
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

    status_updates_queue.put_nowait(
        gui.ReadConnectionStateChanged.INITIATED
    )

    while True:
        reader, writer = await connect((host, port))
        status_updates_queue.put_nowait(
            gui.ReadConnectionStateChanged.ESTABLISHED
        )
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
            status_updates_queue.put_nowait(
                gui.ReadConnectionStateChanged.CLOSED
            )
            writer.close()


async def watch_for_connection(watchdog_queue):
    """Timer to monitor network connection by checking time between packages"""
    while True:
        try:
            async with timeout(2):
                message = await watchdog_queue.get()
                watchdog_logger.info(message)
        except asyncio.TimeoutError:
            watchdog_logger.info('2s timeout is elapsed')
            raise ConnectionError()


# TODO декоратор reconnect, если у вас такой есть в старом коде
async def handle_connection(host, read_port, write_port, history, token,
                            messages_queue, sending_queue, status_updates_queue,
                            logging_queue, watchdog_queue):
    while True:
        async with create_handy_nursery() as nursery:
            try:
                nursery.start_soon(
                    read_messages(
                        host, read_port, history, messages_queue,
                        logging_queue, status_updates_queue, watchdog_queue
                    )
                )

                nursery.start_soon(
                    send_messages(
                        host, write_port, token, sending_queue,
                        status_updates_queue, watchdog_queue
                    )
                )

                nursery.start_soon(watch_for_connection(watchdog_queue))

            except aionursery.MultiError as e:
                # TODO: that doesn't catch the exception.'read_messages' hangs
                print('aionursery.MultiError')
                print(e.exceptions)
            except Exception as e:
                print('Exception', e)
            else:
                print('handle_connection else part')


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

    except InvalidTokenException:
        # TODO: #11: this actually doesn't work, program doesn't stop gracefully
        print('InvalidTokenException')
        return

    # TODO: #10: add graceful shutdown: KeyboardInterrupt, gui.TkAppClosed
    # except (KeyboardInterrupt, gui.TkAppClosed):
    #     print('exit')
    #     exit()


if __name__ == '__main__':
    asyncio.run(main())
