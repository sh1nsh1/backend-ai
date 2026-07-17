import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from typing import Literal

import colorlog

from config import config


def get_logger(
    name: str,
    level: Literal[10, 20, 30, 40, 50] = 20,
    log_file: str | None = None,
) -> Logger:
    stream_handler = colorlog.StreamHandler()
    colored_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-7s%(reset)s %(asctime)s %(yellow)s%(name)s: %(white)s%(message)s%(reset)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    stream_handler.setFormatter(colored_formatter)

    logger = colorlog.getLogger(name)
    logger.addHandler(stream_handler)

    file_path = log_file or config.log.file
    if file_path:
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=50_000_000,
            backupCount=5,
        )
        plain_formatter = logging.Formatter(
            "%(levelname)-7s %(asctime)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(plain_formatter)
        logger.addHandler(file_handler)

    logger.setLevel(level)
    return logger
