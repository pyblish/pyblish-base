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

from __future__ import absolute_import

import logging
import pyblish

from .plugin import (
    Context, Instance, discover,
    Selector, Validator, Extractor, Conformer,
    plugin_paths, register_plugin_path,
    deregister_plugin_path, deregister_all,
    registered_paths, environment_paths, configured_paths,
    plugins_by_family, plugins_by_host, instances_by_plugin)

from .plugin import Config as __Config
from .lib import log, format_filename
from .error import (
    PyblishError, SelectionError, ValidationError,
    ExtractionError, ConformError, NoInstancesError)

# For forwards-compatibility
Collector = Selector
Integrator = Conformer

# Initialise log
__formatter = logging.Formatter("%(levelname)s - %(message)s")
__handler = logging.StreamHandler()
__handler.setFormatter(__formatter)
__log = logging.getLogger("pyblish")
__log.propagate = True
__log.handlers[:] = []
__log.addHandler(__handler)
__log.setLevel(logging.DEBUG)

if not pyblish.is_initialized():
    try:
        pyblish.config = __Config()
    except Exception as e:
        __log.debug("Exception: %s" % e)
        __log.warning("Something went wrong whilst "
                      "initializing configuration")

config = pyblish.config


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
