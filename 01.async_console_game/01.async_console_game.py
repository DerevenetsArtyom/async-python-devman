import asyncio
import curses
import random
import time

from curses_tools import draw_frame, read_controls

TIC_TIMEOUT = 0.1


async def fire(canvas, start_row, start_column, rows_speed=0, columns_speed=1):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol):
    # while loop needs to be here not to throw StopIteration and work forever...
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        delay = random.randint(1, 20)

        for i in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(delay):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(delay):
            await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, frame1, frame2):
    # while loop needs to be here not to throw StopIteration and work forever...
    while True:
        draw_frame(canvas, row, column, frame1)
        canvas.refresh()
        await asyncio.sleep(0)

        # flush the previous frame before drawing the next one
        draw_frame(canvas, row, column, frame1, negative=True)

        # update coordinates after pressing some arrow
        row, column, _ = read_controls(canvas, row, column)

        draw_frame(canvas, row, column, frame2)
        canvas.refresh()
        await asyncio.sleep(0)


def read_rocket_frames():
    with open("files/rocket_frame_1.txt") as f:
        frame1 = f.read()

    with open("files/rocket_frame_2.txt") as f:
        frame2 = f.read()

    return frame1, frame2


def draw(canvas):
    curses.curs_set(False)  # Set the cursor state. 0 for invisible.

    canvas.nodelay(True)  # If flag is True, getch() will be non-blocking.
    canvas.border()
    canvas.refresh()

    frame1, frame2 = read_rocket_frames()
    canvas_height, canvas_width = canvas.getmaxyx()
    number_of_stars = random.randint(50, 60)

    coroutines = []
    # Add initial action (coroutine) - shot out of a cannon
    # coroutine_fire = fire(canvas, canvas_height // 2, canvas_width // 2)
    # coroutines.append(coroutine_fire)

    # Add action (coroutine) - animate spaceship
    coroutine_rocket = animate_spaceship(
        canvas,
        canvas_height // 2,
        canvas_width // 2,
        frame1, frame2,
    )
    coroutines.append(coroutine_rocket)

    # Form list of coroutines (1 coroutine - 1 star)
    for i in range(number_of_stars):
        # Reducing max dimensions by 2 allows to avoid "curses.error"
        row = random.randint(1, canvas_height - 2)
        column = random.randint(1, canvas_width - 2)

        symbol = random.choice("+*.:")

        coroutine = blink(canvas, row, column, symbol)
        coroutines.append(coroutine)

    while True:
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            # 'coroutine_fire' could raise StopIteration when reach the borders
            except StopIteration:
                coroutines.remove(coroutine)

        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
