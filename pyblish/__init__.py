import logging

from .version import *


def get_formatter():
    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s',
        '%H:%M:%S')
    return formatter


def setup_log():
    log = logging.getLogger('pyblish')

    if log.handlers:
        return log.handlers[0]

    log.setLevel(logging.DEBUG)
    # log.setLevel(logging.INFO)
    # log.setLevel(logging.WARNING)

    formatter = get_formatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log
