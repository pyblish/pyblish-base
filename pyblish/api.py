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

import logging
import pyblish

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


def __init__():
    pyblish.config = __Config()

    # Initialise log
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log = logging.getLogger("pyblish")
    log.propagate = True
    log.handlers[:] = []
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

__init__()

version = pyblish.version
config = pyblish.config


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
    "register_plugin_path",
    "deregister_plugin_path",
    "deregister_all_paths",
    "register_plugin",
    "deregister_plugin",
    "registered_plugins",
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

    # Decorators
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
