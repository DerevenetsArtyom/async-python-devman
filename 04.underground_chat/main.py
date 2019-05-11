import asyncio

SERVER_HOST = 'minechat.dvmn.org'
SERVER_PORT = 5000


async def tcp_client():
    reader, writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)

    while True:
        data = await reader.read(100)
        print(f'Received: {data.decode()!r}')

loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_client())
loop.close()
