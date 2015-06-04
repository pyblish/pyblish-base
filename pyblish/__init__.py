"""Pyblish initialisation

Attributes:
    config: Currently active instance of configuration.
    _registered_paths: Currently registered plug-in paths.
    _registered_plugins: Currently registered plug-ins.

"""

from .version import *


_registered_paths = list()
_registered_plugins = dict()
_registered_services = dict()
_registered_test = None
