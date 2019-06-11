import argparse
import asyncio
import logging
import os

from dotenv import load_dotenv

import gui
from chat_utils import submit_message, authorise, connect
from files_utils import load_from_log_file, save_messages_to_file


async def send_messages(host, write_port, token, sending_queue):
    # XXX: before every send we call 'authorise' and check token. Is that OK?
    while True:
        reader, writer = await connect((host, write_port))

        try:
            await reader.readline()

            if token:
                token_is_valid = await authorise(reader, writer, token)
                if token_is_valid:
                    # Override token in env to be able to send messages
                    # without explicit token for next requests
                    os.environ["TOKEN"] = token

                    message = await sending_queue.get()
                    await submit_message(reader, writer, message)
                else:
                    print("Invalid token. Check it or register again")

        finally:
            writer.close()


async def read_messages(host, port, history, messages_queue, logging_queue):
    """
    Read messages from the remote server and put it
    in 'messages_queue' to be displayed in GUI afterwards.
    Also put messages in 'logging_queue' to save it to log file.
    If there is any messages already in the log file - display it first in GUI.
    """

    await load_from_log_file(history, messages_queue)

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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    load_dotenv()
    args = get_arguments(
        os.getenv('SERVER_HOST'),
        os.getenv('SERVER_READ_PORT'),
        os.getenv('SERVER_WRITE_PORT'),
        os.getenv('TOKEN'),
        os.getenv('HISTORY'),
        # os.getenv('USERNAME'),
    )

    # TODO: add graceful shutdown
    asyncio.run(start(**args))


if __name__ == '__main__':
    main()
