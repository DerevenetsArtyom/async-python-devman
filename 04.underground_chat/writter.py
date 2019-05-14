import argparse
import asyncio
import os
import json

SERVER_HOST = 'minechat.dvmn.org'
SERVER_WRITE_PORT = 5050
TOKEN = '5210a154-74ca-11e9-9d4f-0242ac110002'


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


async def tcp_client(server, history, token):
    reader, writer = await connect(server)

    data = await reader.readline()  # 'Hello %username%!
    print(f'Received: {data.decode()!r}')

    message = token + '\n'
    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()  # {"nickname": ... , "account_hash": ...}
    print(f'Received: {data.decode()!r}')

    response = json.loads(data.decode())
    if not response:
        print("Неизвестный токен. Проверьте его или зарегистрируйте заново")
        return

    data = await reader.readline()  # Welcome to chat! Post your message below.
    print(f'Received: {data.decode()!r}')

    message = 'Hello from Python\n\n'

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()  # Message send. Write more
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()


def main():
    parser = argparse.ArgumentParser()
    # TODO: add help strings
    parser.add_argument('--host', type=str, help='')
    parser.add_argument('--port', type=str, help='')
    parser.add_argument('--history', type=str, help='')
    parser.add_argument('--token', type=str, help='')
    args = parser.parse_args()

    host = args.host or os.getenv('CHAT_HOST', SERVER_HOST)
    port = args.port or os.getenv('CHAT_PORT', SERVER_WRITE_PORT)
    token = args.token or os.getenv('TOKEN', TOKEN)
    history = args.history or os.getenv('HISTORY', 'minechat-history.txt')
    server = (host, port)

    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    loop.run_until_complete(tcp_client(server, history, token))
    loop.close()


if __name__ == '__main__':
    main()
