import argparse
import asyncio
import logging
import os

import aiofiles
from dotenv import load_dotenv

from constants import SERVER_READ_PORT, SERVER_HOST, HISTORY
from helpers import connect, log_to_file


async def tcp_client(host, port, history):
    while True:
        try:
            reader, writer = await connect((host, port), history)

            async with aiofiles.open(history, 'a') as file:
                while True:
                    data = await reader.readline()
                    await log_to_file(data.decode(), file)

        except Exception as e:
            logging.info(e)
            continue
        finally:
            writer.close()


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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s: %(message)s',
        datefmt='%H:%M:%S',
    )
    load_dotenv()
    args = get_arguments(
        os.getenv('SERVER_HOST', SERVER_HOST),
        os.getenv('SERVER_READ_PORT', SERVER_READ_PORT),
        os.getenv('HISTORY', HISTORY),
    )
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(tcp_client(**args))
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()


if __name__ == '__main__':
    main()
