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

from . import version
import getpass
import os

from .plugin import (
    Context,
    Instance,

    Action,
    Category,
    Separator,

    # Matching algorithms
    Subset,
    Intersection,
    Exact,

    Asset,
    Plugin,
    Validator,
    Extractor,
    Integrator,
    Collector,
    discover,

    ContextPlugin,
    InstancePlugin,

    CollectorOrder,
    ValidatorOrder,
    ExtractorOrder,
    IntegratorOrder,

    register_host,
    registered_hosts,
    deregister_host,
    deregister_all_hosts,

    current_target,
    register_target,
    registered_targets,
    deregister_target,
    deregister_all_targets,

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

    register_callback,
    deregister_callback,
    deregister_all_callbacks,
    registered_callbacks,

    register_discovery_filter,
    deregister_discovery_filter,
    deregister_all_discovery_filters,
    registered_discovery_filters,

    sort as sort_plugins,

    registered_paths,
    environment_paths,
    current_host,
)

from .lib import (
    log,
    time as __time,
    emit,
    main_package_path as __main_package_path
)

from .logic import (
    plugins_by_family,
    plugins_by_host,
    plugins_by_instance,
    plugins_by_targets,
    instances_by_plugin,
    register_test,
    deregister_test,
    registered_test,

    register_gui,
    registered_guis,
    deregister_gui,

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
    Selector,
    Conformer,
    format_filename,
)


def __init__():
    """Initialise Pyblish

    This function registered default services,
    hosts and tests. It is idempotent and thread-safe.

    """

    # Register default services
    register_service("time", __time)
    register_service("user", getpass.getuser())
    register_service("context", None)
    register_service("instance", None)

    # Register default host
    register_host("python")

    # Register hosts from environment "PYBLISHHOSTS"
    for host in os.environ.get("PYBLISH_HOSTS", "").split(os.pathsep):
        if not host:
            continue

        register_host(host)

    # Register targets for current session
    for target in os.environ.get("PYBLISH_TARGETS", "").split(os.pathsep):
        if not target:
            continue

        register_target(target)

    # Register default path
    register_plugin_path(os.path.join(__main_package_path(), "plugins"))

    # Register default test
    register_test(__default_test)


__init__()


__all__ = [
    # Base objects
    "Context",
    "Instance",
    "Asset",

    # Matching algorithms
    "Subset",
    "Intersection",
    "Exact",

    "Plugin",
    "Action",
    "Category",
    "Separator",

    # SVEC plug-ins
    "Collector",
    "Selector",
    "Validator",
    "Extractor",
    "Conformer",
    "Integrator",

    "ContextPlugin",
    "InstancePlugin",

    "CollectorOrder",
    "ValidatorOrder",
    "ExtractorOrder",
    "IntegratorOrder",

    # Plug-in utilities
    "discover",

    "plugin_paths",
    "registered_paths",
    "environment_paths",

    "register_host",
    "registered_hosts",
    "deregister_host",
    "deregister_all_hosts",

    "register_plugin",
    "deregister_plugin",
    "deregister_all_plugins",
    "registered_plugins",

    "register_service",
    "deregister_service",
    "deregister_all_services",
    "registered_services",

    "register_callback",
    "deregister_callback",
    "deregister_all_callbacks",
    "registered_callbacks",

    "register_plugin_path",
    "deregister_plugin_path",
    "deregister_all_paths",

    "register_test",
    "deregister_test",
    "registered_test",

    "register_gui",
    "registered_guis",
    "deregister_gui",

    "plugins_by_family",
    "plugins_by_host",
    "plugins_by_instance",
    "instances_by_plugin",

    "current_target",
    "register_target",
    "registered_targets",
    "deregister_target",
    "deregister_all_targets",

    "sort_plugins",
    "format_filename",
    "current_host",
    "sort_plugins",

    "version",

    # Utilities
    "log",
    "emit",

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
