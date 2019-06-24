"""Pyblish initialisation

Attributes:
    _registered_paths: Currently registered plug-in paths.
    _registered_plugins: Currently registered plug-ins.

"""

from .version import version, version_info, __version__


_registered_paths = list()
_registered_callbacks = dict()
_registered_plugins = dict()
_registered_services = dict()
_registered_test = dict()
_registered_hosts = list()
_registered_targets = list()
_registered_gui = list()
_registered_plugin_filters = list()


__all__ = [
    "version",
    "version_info",
    "__version__",
    "_registered_paths",
    "_registered_callbacks",
    "_registered_plugins",
    "_registered_services",
    "_registered_test",
    "_registered_hosts",
    "_registered_targets",
    "_registered_gui",
    "_registered_plugin_filters"
]
