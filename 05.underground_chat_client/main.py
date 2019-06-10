import argparse
import asyncio
import os

import aiofiles
from dotenv import load_dotenv

import gui
from helpers import connect, log_to_file, display_from_log_file


# Программе понадобятся несколько параллельных задач —
# одна рисует окно интерфейса,
# другая слушает сервер,
# третья отравляет сообщения.


async def save_messages_to_file(filepath, logging_queue):
    """Wait until 'logging_queue' has any message and write it to log file"""
    async with aiofiles.open(filepath, 'a') as file:
        while True:
            message = await logging_queue.get()
            await log_to_file(message, file)


async def send_messages(host, port, sending_queue):
    while True:
        message = await sending_queue.get()
        print(message)


async def read_messages(host, port, history, messages_queue, logging_queue):
    """
    Read messages from the remote server and put it in 'messages_queue' to be
    displayed in GUI afterwards.
    Also put messages in 'logging_queue' to save it to log file.
    If there is any messages in log file - display it first in GUI.
    """

    await display_from_log_file(history, messages_queue)

    while True:
        reader, writer = await connect((host, port))
        try:
            while True:
                data = await reader.readline()
                message = data.decode()
                messages_queue.put_nowait(message.strip())
                logging_queue.put_nowait(message)

        except Exception as e:
            print(e)
            continue
        finally:
            writer.close()


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

    await asyncio.gather(
        gui.draw(messages_queue, sending_queue, status_updates_queue),

        read_messages(host, read_port, history, messages_queue, logging_queue),
        send_messages(host, write_port, token, sending_queue),
        save_messages_to_file(history, logging_queue),
    )


def get_arguments(host, read_port, write_port, token, history):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Host to connect')
    parser.add_argument('--read-port', type=str,
                        help='Port to connect for reading')
    parser.add_argument('--write-port', type=str,
                        help='Port to connect for writting')
    parser.add_argument('--token', type=str, help='Token')
    parser.add_argument('--history', type=str, help='Path to history file')

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
    load_dotenv()
    args = get_arguments(
        os.getenv('SERVER_HOST'),
        os.getenv('SERVER_READ_PORT'),
        os.getenv('SERVER_WRITE_PORT'),
        os.getenv('TOKEN'),
        os.getenv('HISTORY'),
        # os.getenv('USERNAME'),
    )

    asyncio.run(start(**args))


if __name__ == '__main__':
    main()
