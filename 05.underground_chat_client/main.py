import asyncio
import time
import gui

# Программе понадобятся несколько параллельных задач —
# одна рисует окно интерфейса,
# другая слушает сервер,
# третья отравляет сообщения.


async def generate_messages(queue):
    while True:
        message = f'Ping {int(time.time())}'
        queue.put_nowait(message)
        await asyncio.sleep(1)


async def main():
    # Queues must be created inside the loop.
    # If create them outside the loop created for asyncio.run(),
    # so they use events.get_event_loop().
    # asyncio.run() creates a new loop, and futures created for the queue
    # in one loop can't then be used in the other.
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        generate_messages(messages_queue),
        gui.draw(messages_queue, sending_queue, status_updates_queue)
    )

asyncio.run(main())
