import asyncio
import curses
import random
import time

from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1


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
    canvas_max_height, canvas_max_width = canvas.getmaxyx()  # (26, 191)
    frame_rows, frame_columns = get_frame_size(frame1)  # (9, 5)

    # while loop needs to be here not to throw StopIteration and work forever...
    while True:
        draw_frame(canvas, row, column, frame1)
        await asyncio.sleep(0)

        # flush the previous frame before drawing the next one
        draw_frame(canvas, row, column, frame1, negative=True)

        # update coordinates after pressing some arrow
        row_diff, column_diff, _ = read_controls(canvas)

        # Horizontal restriction: right <-> left
        if 0 < (column + column_diff) < (canvas_max_width - frame_columns):
            column += column_diff

        # Vertical restriction: up ↕ down
        if 0 < (row + row_diff) < (canvas_max_height - frame_rows):
            row += row_diff

        draw_frame(canvas, row, column, frame2)
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
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)

        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
