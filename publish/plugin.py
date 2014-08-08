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
import sys
import inspect

# Local library
import publish.abstract

__all__ = ['discover',
           'register_plugin_path',
           'deregister_plugin_path']

validator_pattern = re.compile(r'^validate_.*\.py$')
validator_dirs = []


def register_plugin_path(path):
    validator_dirs.append(path)


def deregister_plugin_path(path):
    validator_dirs.remove(path)


def discover(type):
    if type == 'validators':
        return _discover_validators()

    raise ValueError("type not recognised: {0}".format(type))


def _discover_validators():
    """Find and return validators"""

    plugins = list()
    for dname in validator_dirs:
        for fname in os.listdir(dname):
            abspath = os.path.join(dname, fname)

            if not os.path.isfile(abspath):
                continue

            name, suffix = os.path.splitext(fname)

            if validator_pattern.match(fname):
                module = imp.load_source(name, abspath)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        if issubclass(obj, publish.abstract.Validator):
                            plugins.append(obj)

    validated = list()
    while plugins:
        plugin = plugins.pop()
        if _is_valid(plugin):
            validated.append(plugin)
        else:
            sys.stderr.write(
                "Invalid plugin: {0}\n".format(plugin))

    return validated


def _is_valid(plugin):
    try:
        attrs = [
            'families',
            'hosts',
            'version',
            'process',
            'fix']

        for attr in attrs:
            assert attr in dir(plugin)

    except AssertionError:
        return False

    return True


if __name__ == '__main__':
    # Register validators
    module_dir = os.path.dirname(__file__)
    validators_path = os.path.join(module_dir, 'validators')

    register_plugin_path(validators_path)

    # List available validators
    for plugin in discover('validators'):
        print "%s" % plugin
