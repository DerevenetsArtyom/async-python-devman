import time
import curses
import asyncio


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    row = 5
    curses.curs_set(False)
    canvas.border()
    canvas.refresh()

    coroutine1 = blink(canvas, row, 2)
    coroutine2 = blink(canvas, row, 4)
    coroutine3 = blink(canvas, row, 6)
    coroutine4 = blink(canvas, row, 8)
    coroutine5 = blink(canvas, row, 10)

    coroutines = [
      coroutine1, coroutine2, coroutine3, coroutine4, coroutine5,
    ]

    while True:
        for coroutine in coroutines:
            coroutine.send(None)
        time.sleep(0.1)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
