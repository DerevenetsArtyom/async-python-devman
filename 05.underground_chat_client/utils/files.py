import datetime
import logging
import os

import aiofiles

main_logger = logging.getLogger("main_logger")


async def save_messages_to_file(filepath, logging_queue):
    """Wait until 'logging_queue' has any message and write it to log file"""
    async with aiofiles.open(filepath, "a") as file:
        while True:
            message = await logging_queue.get()
            await log_to_file(message, file)


async def log_to_file(message, file):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d %H:%M")

    log = f"[{timestamp}] {message}"
    await file.write(log)

    main_logger.info(message.strip())


async def load_from_log_file(history, messages_queue):
    if os.path.exists(history):
        async with aiofiles.open(history) as file:
            async for line in file:
                messages_queue.put_nowait(line.strip())  # remove \n from line
