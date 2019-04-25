import asyncio
import curses
import random
import time

from provided.curses_tools import draw_frame, read_controls, get_frame_size
from provided.explosion import explode
from provided.obstacles import Obstacle, show_obstacles
from provided.physics import update_speed
from read_frames import (read_garbage_frames, read_rocket_frames,
                         read_game_over_frame)
from utils import sleep, blink

RANGE_OF_STARS = (5, 6)
TIC_TIMEOUT = 0.1
spaceship_frame = ""
obstacles_list = []
coroutines = []
obstacles_in_last_collisions = []


async def fire(canvas, start_row, start_column):
    row = start_row - 1  # Shift up start row not to overlap with rocket frame
    column = start_column + 2  # Adjust to the center of rocket frame

    while 0 < row:
        for obstacle in obstacles_list:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return

        canvas.addstr(round(row), round(column), '|')
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        # Emulate moving from the bottom to the top
        row -= 1


async def show_game_over(canvas, frame):
    canvas_max_height, canvas_max_width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(frame)

    # Place the caption in the center of the screen
    row = (canvas_max_height - frame_rows) // 2
    column = (canvas_max_width - frame_columns) // 2

    while True:
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)


async def run_spaceship(canvas, frame_rows, frame_columns, game_over_frame):
    canvas_max_height, canvas_max_width = canvas.getmaxyx()
    row, column = canvas_max_height // 2, canvas_max_width // 2
    row_speed = column_speed = 0

    while True:
        for obstacle in obstacles_list:
            if obstacle.has_collision(row, column):
                coroutines.append(show_game_over(canvas, game_over_frame))
                return

        draw_frame(canvas, row, column, spaceship_frame)
        old_frame = spaceship_frame
        await asyncio.sleep(0)

        # 'spaceship_frame' could be changed while 'await' works.
        # Flush previous frame (and current)
        draw_frame(canvas, row, column, old_frame, negative=True)

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


async def animate_spaceship(canvas, frame1, frame2, game_over_frame):
    frame_rows, frame_columns = get_frame_size(frame1)

    coroutines.append(
        run_spaceship(canvas, frame_rows, frame_columns, game_over_frame)
    )

    global spaceship_frame
    while True:
        spaceship_frame = frame1
        await asyncio.sleep(0)

        spaceship_frame = frame2
        await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Column position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    rows_size, columns_size = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - columns_size - 2)
    row = 0

    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles_list.append(obstacle)

    # Move obstacle down the screen until it reaches the end of the screen.
    # When reached - remove that obstacle from 'obstacles_list'.
    try:
        while row < rows_number:
            draw_frame(canvas, row, column, garbage_frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            obstacle.row += speed
            row += speed

            # Stop drawing garbage and obstacle frame if it was hit:
            # remove that coroutines from corresponding lists and show explosion
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                await explode(
                    canvas,
                    row + (rows_size // 2),
                    column + (columns_size // 2)
                )
                return
    finally:
        obstacles_list.remove(obstacle)


async def fill_orbit_with_garbage(canvas, small_frame, large_frame):
    _, canvas_width = canvas.getmaxyx()

    while True:
        # Add garbage only 10% of execution time.
        # XXX: I'm not sure that this works totally correctly.
        probability = random.randrange(0, 100)
        if probability < 10:
            garb_frame = random.choice([small_frame, large_frame])
            _, frame_columns = get_frame_size(garb_frame)

            # Try to restrict border values to fill with 'garb_frame' dimensions
            column = random.randint(frame_columns, canvas_width - frame_columns)
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
    game_over_frame = read_game_over_frame()

    rocket_coroutine = animate_spaceship(canvas, frame1, frame2,
                                         game_over_frame)
    coroutines.append(rocket_coroutine)

    fill_orbit_garbage_coroutine = fill_orbit_with_garbage(
        canvas, small_garbage_frame, large_garbage_frame
    )
    coroutines.append(fill_orbit_garbage_coroutine)

    show_obstacles_coroutine = show_obstacles(canvas, obstacles_list)
    coroutines.append(show_obstacles_coroutine)

    canvas_height, canvas_width = canvas.getmaxyx()
    number_of_stars = random.randint(*RANGE_OF_STARS)

    # Form list of coroutines (1 coroutine - 1 star)
    for i in range(number_of_stars):
        # Reducing max dimensions by 2 allows to avoid "curses.error"
        row = random.randint(1, canvas_height - 2)
        column = random.randint(1, canvas_width - 2)

        symbol = random.choice("+*.:")
        offset_tics = random.randint(1, 20)

        coroutine = blink(canvas, row, column, symbol, offset_tics)
        coroutines.append(coroutine)

    while True:
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
