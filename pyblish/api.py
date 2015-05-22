"""Expose common functionality

Use this in plugins, integrations and extensions of Pyblish.
This part of the library is what will change the least and
attempt to maintain backwards- and forwards-compatibility.

This way, we as developers are free to refactor the library
without breaking any of your tools.

.. note:: Contributors, don't use this in any other module internal
    to Pyblish or a cyclic dependency will be created. This is only
    to be used by end-users of the library and from
    integrations/extensions of Pyblish.

"""

from __future__ import absolute_import

import getpass
import logging
import pyblish
import datetime

from .plugin import (
    Context,
    Instance,
    Selector,
    Validator,
    Extractor,
    Conformer,
    Config as __Config,
    discover,

    register_plugin,
    deregister_plugin,
    deregister_all_plugins,
    registered_plugins,

    plugin_paths,
    register_plugin_path,
    deregister_plugin_path,
    deregister_all_paths,

    register_service,
    deregister_service,
    deregister_all_services,
    registered_services,

    plugins_by_family,
    plugins_by_host,
    plugins_by_instance,
    instances_by_plugin,

    sort as sort_plugins,

    registered_paths,
    environment_paths,
    configured_paths,
    current_host,
)

from .lib import (
    log,
    format_filename
)

from .error import (
    PyblishError,
    SelectionError,
    ValidationError,
    ExtractionError,
    ConformError,
    NoInstancesError
)

from .compat import (
    deregister_all,
    sort,
)

# Aliases
Collector = Selector
Integrator = Conformer

version = pyblish.version
config = None


def __init__():
    pyblish.config.update(__Config())

    # Enable access to configuration through API
    global config
    config = pyblish.config

    # Initialise log
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log = logging.getLogger("pyblish")
    log.propagate = True
    log.handlers[:] = []
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    # Register default services
    def time():
        return datetime.datetime.now().strftime(config["date_format"])

    register_service("time", time)
    register_service("user", getpass.getuser)
    register_service("context", None)
    register_service("instance", None)

__init__()


__all__ = [
    # Base objects
    "Context",
    "Instance",

    # SVEC plug-ins
    "Collector",
    "Selector",
    "Validator",
    "Extractor",
    "Conformer",
    "Integrator",

    # Plug-in utilities
    "discover",

    "plugin_paths",
    "registered_paths",
    "configured_paths",
    "environment_paths",

    "register_plugin",
    "deregister_plugin",
    "deregister_all_plugins",
    "registered_plugins",

    "register_service",
    "deregister_service",
    "deregister_all_services",
    "registered_services",

    "register_plugin_path",
    "deregister_plugin_path",
    "deregister_all_paths",

    "plugins_by_family",
    "plugins_by_host",
    "plugins_by_instance",
    "instances_by_plugin",

    "sort_plugins",
    "format_filename",
    "current_host",
    "sort_plugins",

    # Configuration
    "config",
    "version",

    # Utilities
    "log",

    # Exceptions
    "PyblishError",
    "SelectionError",
    "ValidationError",
    "ExtractionError",
    "ConformError",
    "NoInstancesError",

    # Compatibility
    "deregister_all",
    "sort",
]
