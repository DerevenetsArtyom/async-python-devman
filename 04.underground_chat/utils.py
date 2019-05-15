import asyncio


def sanitize(message):
    return message.replace('\n', '').replace('\r', '')


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
