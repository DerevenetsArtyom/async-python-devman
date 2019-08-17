import logging


def setup_logger(
    logger_name,
    log_file=None,
    level=logging.INFO,
    fmt="%(asctime)s: %(message)s",
    datefmt="%H:%M:%S",
):
    if not log_file:
        log_file = f"{logger_name}.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    file_handler = logging.FileHandler(log_file)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
