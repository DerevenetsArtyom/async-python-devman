import argparse
import asyncio
import os

import aiofiles
from dotenv import load_dotenv

import gui
from helpers import connect, log_to_file

# Программе понадобятся несколько параллельных задач —
# одна рисует окно интерфейса,
# другая слушает сервер,
# третья отравляет сообщения.

SERVER_HOST = 'minechat.dvmn.org'
SERVER_WRITE_PORT = 5050
SERVER_READ_PORT = 5000
HISTORY = 'history.txt'


async def save_messages_to_file(filepath, queue):
    async with aiofiles.open(filepath, 'a') as file:
        while True:
            message = await queue.get()  # wait until an item is available
            await log_to_file(message, file)


async def read_messages(host, port, history, messages_queue, logging_queue):
    async with aiofiles.open(history) as file:
        async for line in file:
            messages_queue.put_nowait(line.strip())  # remove \n from line

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


async def start(host, port, history):
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
        read_messages(host, port, history, messages_queue, logging_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue),
        save_messages_to_file(history, logging_queue)
    )


def get_arguments(host, port, history):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Host to connect')
    parser.add_argument('--port', type=str, help='Port to connect')
    parser.add_argument('--history', type=str, help='Path to history file')

    parser.set_defaults(
        host=host,
        port=port,
        history=history,
    )
    args = parser.parse_args()
    return vars(args)


def main():
    load_dotenv()
    args = get_arguments(
        os.getenv('CHAT_HOST', SERVER_HOST),
        os.getenv('SERVER_READ_PORT', SERVER_READ_PORT),
        os.getenv('HISTORY', HISTORY),
    )

    asyncio.run(start(**args))


if __name__ == '__main__':
    main()
