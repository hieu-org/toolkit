import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import colorlog
from colorlog import ColoredFormatter

from .constant import FTIME_YYYYMMDD


class HTimedRotatingFileHandler(TimedRotatingFileHandler):

    def rotate(self, source, dest):
        # Get the logger instance
        logger = logging.getLogger()

        # Find the FileHandler in the logger's handlers
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        if file_handler is not None:
            # Remove the FileHandler from the logger's handlers
            logger.removeHandler(file_handler)

            # Set the new filename for the FileHandler
            new_filename = os.path.join(
                os.path.dirname(source),
                f"{Path(source).stem}.{datetime.today().strftime(FTIME_YYYYMMDD)}"
            )
            file_handler.baseFilename = new_filename
            file_handler.filename = new_filename

            # Add the FileHandler back to the logger's handlers
            logger.addHandler(file_handler)


def new_colored_formatter(info_color='white'):
    formatter = ColoredFormatter(
        '%(log_color)s%(levelname)s:%(name)s:%(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': info_color,
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_black',
        },
        secondary_log_colors={},
        style='%')
    return formatter


def new_colored_handler(info_color='white'):
    formatter = new_colored_formatter(info_color)

    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)

    return handler


def new_colored_logger(name: str, info_color='white'):
    handler = new_colored_handler(info_color)

    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def new_stdout_logger(name: str):
    logger = logging.getLogger(name)
    logger.propagate = False
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter('%(levelname)-5.5s [%(name)s] - %(message)s')
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    logger.setLevel('INFO')
    return logger
