import argparse
import asyncio
import os

SERVER_HOST = 'minechat.dvmn.org'
SERVER_WRITE_PORT = 5050
TOKEN = '5210a154-74ca-11e9-9d4f-0242ac110002'

# Hello %username%! Enter your personal hash or leave it empty to create new account.
# 5210a154-74ca-11e9-9d4f-0242ac110002
# {"nickname": "Boring karkadee", "account_hash": "5210a154-74ca-11e9-9d4f-0242ac110002"}
# Welcome to chat! Post your message below. End it with an empty line.
# hollee


async def connect(server):
    """Set up re-connection for client"""
    while True:
        try:
            reader, writer = await asyncio.open_connection(*server)
            return reader, writer
        except (ConnectionRefusedError, ConnectionResetError) as e:
            print(e)
            print("Server not up retrying in 5 seconds...")
            await asyncio.sleep(5)


async def tcp_client(server, history):
    reader, writer = await connect(server)
    data = await reader.readline()
    print(f'Received: {data.decode()!r}')

    message = TOKEN + '\n'
    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    print(data.decode())
    print(f'Received: {data.decode()!r}')

    message = 'Hello from Python'

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    print('Close the connection')
    writer.close()


def main():
    parser = argparse.ArgumentParser()
    # TODO: add help strings
    parser.add_argument('--host', type=str, help='')
    parser.add_argument('--port', type=str, help='')
    parser.add_argument('--history', type=str, help='')
    args = parser.parse_args()

    host = args.host or os.getenv('CHAT_HOST', SERVER_HOST)
    port = args.port or os.getenv('CHAT_PORT', SERVER_WRITE_PORT)
    history = args.history or os.getenv('HISTORY', 'minechat-history.txt')
    server = (host, port)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tcp_client(server, history))
    loop.close()


if __name__ == '__main__':
    main()
