import asyncio
import curses
import random
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from global_vars import coroutines
from obstacles import Obstacle, show_obstacles
from physics import update_speed
from read_frames import read_garbage_frames, read_rocket_frames

TIC_TIMEOUT = 0.1
obstacles_list = []


async def fire(canvas, start_row, start_column):
    row = start_row - 1  # Shift up start row not to overlap with rocket frame
    column = start_column + 2  # Adjust to the center of rocket frame

    # TODO: it was here, but I'm not sure if that is needed:
    #  curses.beep()

    while 0 < row:
        canvas.addstr(round(row), round(column), '|')
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row -= 1  # Emulate moving from the bottom to the top


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


async def run_spaceship(canvas, frame_rows, frame_columns):
    canvas_max_height, canvas_max_width = canvas.getmaxyx()  # (26, 191)
    row, column = canvas_max_height // 2, canvas_max_width // 2
    row_speed = column_speed = 0

    while True:
        draw_frame(canvas, row, column, spaceship_frame)
        await asyncio.sleep(0)

        # old_frame = spaceship_frame
        # XXX: 'spaceship_frame' будет успевать измениться за время работы await
        # Стирайте старый кадр, а не текущий.
        # (flush the previous frame before drawing the next one)
        draw_frame(canvas, row, column, spaceship_frame, negative=True)

        # update coordinates after pressing some arrow key
        row_diff, column_diff, space_pressed = read_controls(canvas)

        if space_pressed:
            coroutines.append(fire(canvas, row, column))

        row_speed, column_speed = update_speed(
            row_speed, column_speed,
            row_diff, column_diff
        )

        # Horizontal restriction: right <-> left
        if 0 < (column + column_speed) < (canvas_max_width - frame_columns):
            column += column_speed

        # Vertical restriction: up ↕ down
        if 0 < (row + row_speed) < (canvas_max_height - frame_rows):
            row += row_speed

        draw_frame(canvas, row, column, spaceship_frame)
        await asyncio.sleep(0)


async def animate_spaceship(canvas, frame1, frame2):
    frame_rows, frame_columns = get_frame_size(frame1)  # (9, 5)

    coroutines.append(
        run_spaceship(canvas, frame_rows, frame_columns)
    )

    global spaceship_frame
    while True:
        spaceship_frame = frame1
        await asyncio.sleep(0)

        spaceship_frame = frame2
        await asyncio.sleep(0)


# Советы
#   Если рамка полностью затирает мусор, то обновите код функции draw_frame().

async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    rows_size, columns_size = get_frame_size(garbage_frame)  # (9, 5)

    column = max(column, 0)
    column = min(column, columns_number - columns_size - 2)
    row = 0

    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles_list.append(obstacle)

    coro = show_obstacles(canvas, obstacles_list)
    coroutines.append(coro)

    # Move obstacle down the screen until it reaches the end of the screen.
    # When reached - remove that obstacle from 'obstacles_list'.
    while obstacle.row < rows_number:
        obstacle.row += speed
        await asyncio.sleep(0)

    obstacles_list.remove(obstacle)


async def fill_orbit_with_garbage(canvas, small_frame, large_frame):
    _, canvas_width = canvas.getmaxyx()  # (26, 191)

    while True:
        # Add garbage only 10% of execution time.
        # XXX: I'm not sure that this works totally correctly.
        probability = random.randrange(0, 100)
        if probability < 10:
            garb_frame = random.choice([small_frame, large_frame])

            # Try to restrict border values to fill with 'garb_frame' dimensions
            column = random.randint(15, canvas_width - 10)
            fly_garbage_coroutine = fly_garbage(canvas, column, garb_frame)
            coroutines.append(fly_garbage_coroutine)

        # If there is no desired probability - return control
        else:
            await sleep(1)


def draw(canvas):
    curses.curs_set(False)  # Set the cursor state. 0 for invisible.
    canvas.nodelay(True)  # If flag is True, getch() will be non-blocking.

    # Read files (blocking I/O) before passing it to the event loop
    frame1, frame2 = read_rocket_frames()
    small_garbage_frame, large_garbage_frame = read_garbage_frames()

    canvas_height, canvas_width = canvas.getmaxyx()
    number_of_stars = random.randint(5, 6)

    # Add action (coroutine) - animate spaceship
    rocket_coroutine = animate_spaceship(canvas, frame1, frame2)
    coroutines.append(rocket_coroutine)

    fill_orbit_garbage_coroutine = fill_orbit_with_garbage(
        canvas, small_garbage_frame, large_garbage_frame
    )
    coroutines.append(fill_orbit_garbage_coroutine)

    # Form list of coroutines (1 coroutine - 1 star)
    for i in range(number_of_stars):
        # Reducing max dimensions by 2 allows to avoid "curses.error"
        row = random.randint(1, canvas_height - 2)
        column = random.randint(1, canvas_width - 2)

        symbol = random.choice("+*.:")

        coroutine = blink(canvas, row, column, symbol)
        coroutines.append(coroutine)

    while True:
        # canvas.addstr(5, 5, str(len(coroutines)))
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
