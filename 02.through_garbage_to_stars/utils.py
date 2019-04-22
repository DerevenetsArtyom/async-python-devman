import asyncio
import curses
import random


async def sleep(tics):
    for i in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol):
    # while loop needs to be here not to throw StopIteration and work forever...
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        delay = random.randint(1, 20)

        await sleep(delay)

        canvas.addstr(row, column, symbol)
        await sleep(delay)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(delay)

        canvas.addstr(row, column, symbol)
        await sleep(delay)
