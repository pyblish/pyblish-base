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
import pyblish

from .plugin import (
    Context,
    Instance,
    Asset,
    Plugin,
    Selector,
    Validator,
    Extractor,
    Conformer,
    Integrator,  # Alias
    Collector,  # Alias
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

    sort as sort_plugins,

    registered_paths,
    environment_paths,
    configured_paths,
    current_host,
)

from .lib import (
    log,
    time as __time,
    format_filename,
)

from .logic import (
    plugins_by_family,
    plugins_by_host,
    plugins_by_instance,
    instances_by_plugin,
    register_test,
    deregister_test,
    registered_test,
    default_test as __default_test,
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


version = pyblish.version
config = __Config()


def __init__():
    # Register default services
    register_service("time", __time)
    register_service("user", getpass.getuser())
    register_service("config", config)
    register_service("context", None)
    register_service("instance", None)

    # Register default test
    register_test(__default_test)

__init__()


__all__ = [
    # Base objects
    "Context",
    "Instance",
    "Asset",

    "Plugin",

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

    "register_test",
    "deregister_test",
    "registered_test",

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
