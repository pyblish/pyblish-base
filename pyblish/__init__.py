"""Pyblish initialisation

Attributes:
    config: Currently active instance of configuration.
    manager: Currently active plug-in manager.
    _registered_paths: Currently registered plug-in paths.

"""

from .version import *


config = {}
manager = None

_registered_paths = list()


def is_initialized():
    return True if config else False
