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

from .backend.plugin import (
    Context, Instance, discover,
    Selector, Validator, Extractor, Conformer,
    plugin_paths, register_plugin_path,
    deregister_plugin_path, deregister_all,
    registered_paths, environment_paths, configured_paths)

from . import Config
from .backend.lib import log

# For forwards-compatibility
Integrator = Conformer

config = Config()

__all__ = [
    'Context',
    'Instance',

    'Selector',
    'Validator',
    'Extractor',
    'Conformer',

    'discover',

    'plugin_paths',
    'registered_paths',
    'configured_paths',
    'environment_paths',
    'register_plugin_path',
    'deregister_plugin_path',
    'deregister_all',

    'config',

    'log'
]
