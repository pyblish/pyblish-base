"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate_" and ends with ".py"

Attributes:
    validator_pattern: Predicate for w

"""

# Standard library
import os
import re
import imp
import logging
import inspect

# Local library
import publish.abstract

__all__ = ['discover',
           'register_plugin_path',
           'deregister_plugin_path',
           'deregister_all']

validator_pattern = re.compile(r'^validate_.*\.py$')
validator_dirs = set()

log = logging.getLogger('publish.plugin')


def register_plugin_path(path):
    validator_dirs.add(path)


def deregister_plugin_path(path):
    validator_dirs.remove(path)


def deregister_all():
    validator_dirs.clear()


def discover(type):
    if type == 'validators':
        return _discover_validators()

    raise ValueError("type not recognised: {0}".format(type))


def _discover_validators():
    """Find and return validators"""

    plugins = set()
    for path in validator_dirs:
        for fname in os.listdir(path):
            abspath = os.path.join(path, fname)

            if not os.path.isfile(abspath):
                continue

            name, suffix = os.path.splitext(fname)

            if validator_pattern.match(fname):
                try:
                    module = imp.load_source(name, abspath)
                except ImportError:
                    log.warning("Skipping {0}".format(fname))
                    continue

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        if issubclass(obj, publish.abstract.Filter):
                            plugins.add(obj)

    validated = set()
    while plugins:
        plugin = plugins.pop()
        if _is_valid(plugin):
            validated.add(plugin)
        else:
            log.warning("Invalid plugin: {0}".format(plugin))

    return validated


def _is_valid(plugin):
    try:
        attrs = [
            '__families__',
            '__hosts__',
            '__version__',
            'process',
            'fix']

        for attr in attrs:
            assert attr in dir(plugin)

    except AssertionError:
        return False

    return True
