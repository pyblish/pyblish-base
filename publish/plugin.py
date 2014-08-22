"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate_" and ends with ".py"

Attributes:
    patterns: Regular expressions used for lookup of plugins.
    registered: Set of all registered plugin-paths

"""

# Standard library
import os
import re
import imp
import logging
import inspect

# Local library
import publish.config
import publish.abstract

__all__ = ['discover',
           'register_plugin_path',
           'deregister_plugin_path',
           'deregister_all']

patterns = {
    'validators': publish.config.validators_regex,
    'extractors': publish.config.extractors_regex,
    'selectors': publish.config.selectors_regex,
    'conforms': publish.config.conforms_regex
}

registered = set()

log = logging.getLogger('publish.plugin')


def register_plugin_path(path):
    """Plug-ins are looked up at run-time from directories registered here

    To register a new directory, run this command along with the absolute
    path to where you're plug-ins are located.

    Example:
        >>> my_plugins = '/home/marcus/publish_plugins'
        >>> register_plugin_path(my_plugins)

    """
    registered.add(path)


def deregister_plugin_path(path):
    """Remove a registered path

    Raises:
        KeyError if `path` isn't registered

    """

    registered.remove(path)


def deregister_all():
    """Mainly used in tests"""
    registered.clear()


def discover(type=None, regex=None):
    """Find plugins within registered plugin-paths

    Arguments:
        type (str): Only return plugins of specified type
            E.g. validators, extractors. In None is
            specified, return all plugins.
        regex (str): Limit results to those matching `regex`
            Mathching is done on classes, as opposed to
            filenames due to a file possibly hosting
            multiple plugins.

    """

    if not type:
        plugins = list()
        for type in patterns.keys():
            plugins.extend(_discover_type(type=type,
                                          regex=regex))
        return plugins
    else:
        return _discover_type(type=type, regex=regex)


def _discover_type(type, regex=None):
    """Return plugins of type `type`

    Helper method for the above function :func:discover()

    """

    try:
        plugins = set()

        paths = list(registered)

        # Accept paths added via Python and
        # paths via environment variable.
        env_var = publish.config.paths_environment_variable
        env_val = os.environ.get(env_var)
        if env_val:
            print env_val
            sep = ';' if os.name == 'nt' else ':'
            paths.extend(env_val.split(sep))

        for path in paths:
            for fname in os.listdir(path):
                abspath = os.path.join(path, fname)

                if not os.path.isfile(abspath):
                    continue

                name, suffix = os.path.splitext(fname)

                try:
                    pattern = patterns[type]
                except KeyError:
                    raise  # Handled below

                if re.match(pattern, fname):
                    try:
                        module = imp.load_source(name, abspath)
                    except (ImportError, IndentationError) as e:
                        log.warning('"{mod}": Skipped ({msg})'.format(
                            mod=name, msg=e))
                        continue

                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj):
                            if issubclass(obj, publish.abstract.Filter) or \
                               issubclass(obj, publish.abstract.Selector):
                                if regex is None or re.match(regex,
                                                             obj.__name__):
                                    plugins.add(obj)

        return plugins

    except KeyError:
        raise ValueError("type not recognised: {0}".format(type))


# Register included plugin path
_package_dir = os.path.dirname(__file__)
_validators_path = os.path.join(_package_dir, 'plugins')
_validators_path = os.path.abspath(_validators_path)
register_plugin_path(_validators_path)


if __name__ == '__main__':
    logging.basicConfig()

    # for plugin in discover('extractors'):
    for plugin in discover():
        print plugin
