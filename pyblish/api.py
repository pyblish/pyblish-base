"""Expose common functionality

Use this in plugins, integrations and extensions of Pyblish.
This part of the library is what will change the least and
attempt to maintain backwards- and forwards-compatibility.

This way, we as developers are free to refactor the library
without breaking any of your tools.

.. note:: Don't use this in any other module internal to Pyblish
    or a cyclic dependency will be created. This is only to be used
    by end-users of the library and from integrations/extensions
    of Pyblish.

"""

from .plugin import (
    Context, Instance, discover,
    Selector, Validator, Extractor, Conformer,
    plugin_paths, register_plugin_path,
    deregister_plugin_path, deregister_all,
    registered_paths, environment_paths, configured_paths,
    plugins_by_family, plugins_by_host, instances_by_plugin)

from . import Config as _Config
from .lib import log, format_filename
from .error import (
    PyblishError, SelectionError, ValidationError,
    ExtractionError, ConformError, NoInstancesError)

# For forwards-compatibility
Integrator = Conformer

config = _Config()

__all__ = [
    # Base objects
    'Context',
    'Instance',

    # Plug-ins
    'Selector',
    'Validator',
    'Extractor',
    'Conformer',

    # Plug-in utilities
    'discover',
    'plugin_paths',
    'registered_paths',
    'configured_paths',
    'environment_paths',
    'register_plugin_path',
    'deregister_plugin_path',
    'deregister_all',
    'plugins_by_family',
    'plugins_by_host',
    'instances_by_plugin',

    # Configuration
    'config',

    # Decorators
    'log',
    'format_filename',

    # Exceptions
    'PyblishError',
    'SelectionError',
    'ValidationError',
    'ExtractionError',
    'ConformError',
    'NoInstancesError'
]
