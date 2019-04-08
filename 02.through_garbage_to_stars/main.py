import asyncio
import curses
import random
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from read_frames import read_garbage_frames, read_rocket_frames

TIC_TIMEOUT = 0.1
coroutines = []


async def sleep(tics):
    # TODO: not sure, that this is what was especially needed
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


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def run_asteroid_field(canvas, garbage_frame):
    _, canvas_width = canvas.getmaxyx()

    # Try to restrict border values to fill with 'garbage_frame' dimensions
    column = random.randint(15, canvas_width - 10)
    fly_garbage_coroutine = fly_garbage(canvas, column, garbage_frame)

    await fly_garbage_coroutine


def draw(canvas):
    curses.curs_set(False)  # Set the cursor state. 0 for invisible.

    canvas.nodelay(True)  # If flag is True, getch() will be non-blocking.
    canvas.border()
    canvas.refresh()

    frame1, frame2 = read_rocket_frames()
    small_garbage_frame, large_garbage_frame = read_garbage_frames()

    canvas_height, canvas_width = canvas.getmaxyx()
    number_of_stars = random.randint(50, 60)

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
        # Add garbage only 10% of execution time.
        # I'm not sure that this works totally correct.
        probability = random.randrange(0, 100)
        if probability < 10:
            garb_frame = random.choice([
                small_garbage_frame, large_garbage_frame
            ])
            fly_garbage_coroutine = run_asteroid_field(canvas, garb_frame)
            coroutines.append(fly_garbage_coroutine)

        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
