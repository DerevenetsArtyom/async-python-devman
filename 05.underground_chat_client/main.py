import argparse
import asyncio
import os

from dotenv import load_dotenv

import gui
from helpers import connect

SERVER_HOST = 'minechat.dvmn.org'
SERVER_WRITE_PORT = 5050
SERVER_READ_PORT = 5000


# Программе понадобятся несколько параллельных задач —
# одна рисует окно интерфейса,
# другая слушает сервер,
# третья отравляет сообщения.


async def read_messages(host, port, queue):
    while True:
        try:
            reader, writer = await connect((host, port))

            while True:
                data = await reader.readline()
                queue.put_nowait(data.decode().strip())

        except Exception as e:
            continue
        finally:
            writer.close()


async def start(host, port):
    # Queues must be created inside the loop.
    # If create them outside the loop created for asyncio.run(),
    # so they use events.get_event_loop().
    # asyncio.run() creates a new loop, and futures created for the queue
    # in one loop can't then be used in the other.
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        read_messages(host, port, messages_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue)
    )


def get_arguments(host, port):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Host to connect')
    parser.add_argument('--port', type=str, help='Port to connect')

    parser.set_defaults(
        host=host,
        port=port,
    )
    args = parser.parse_args()
    return vars(args)


def main():
    load_dotenv()
    args = get_arguments(
        os.getenv('CHAT_HOST', SERVER_HOST),
        os.getenv('SERVER_READ_PORT', SERVER_READ_PORT),
    )

    asyncio.run(start(**args))


if __name__ == '__main__':
    main()
