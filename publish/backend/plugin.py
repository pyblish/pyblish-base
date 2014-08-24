"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate_" and ends with ".py"

Attributes:
    patterns: Regular expressions used for lookup of plugins.
    registered_paths: Set of all registered_paths plugin-paths

"""

# Standard library
import os
import re
import sys
import imp
import abc
import logging
import inspect

# Local library
import publish.config
import publish.backend.plugin

__all__ = ['Filter',
           'Selector',
           'Validator',
           'Extractor',
           'Conform',
           'Context',
           'Instance',
           'discover',
           'register_plugin_path',
           'deregister_plugin_path',
           'deregister_all']

patterns = {
    'validators': publish.config.validators_regex,
    'extractors': publish.config.extractors_regex,
    'selectors': publish.config.selectors_regex,
    'conforms': publish.config.conforms_regex
}

registered_paths = set()

log = logging.getLogger('publish.backend.plugin')


class Filter(object):
    """Abstract base-class for sequential plugins

    Sequential plugins are those that takes as input what it gives
    as output and may thus be arranged in any arbitrary order.

    E.g. Validators are filters. Validators may get executed in any
    order whilst still producing identical results. The same goes
    for Extractors.

    """

    __metaclass__ = abc.ABCMeta

    hosts = list()
    version = (0, 0, 0)

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __init__(self):
        self.errors = list()

    @abc.abstractmethod
    def process(self, context):
        """Perform processing upon context `context`

        Returns:
            Generator, yielding per instance

        Yields:
            Tuple of Instance and exception (if any)

        """

        yield None, None


class Selector(Filter):
    """Parse a given working scene for available Instances"""


class Validator(Filter):
    """Validate/check/test individual instance for correctness.

    Raises exception upon failure.

    """

    families = list()

    def fix(self):
        """Optional auto-fix for when validation fails"""


class Extractor(Filter):
    """Physically separate Instance from Host into corresponding Resources

    Yields:
        (Instance, Exception): Output path and exception

    """

    families = list()


class Conform(Filter):
    families = list()


class Context(set):
    """Maintain a collection of Instances"""


class Instance(set):
    """An individually publishable component within scene

    Examples include rigs, models.

    Attributes:
        name (str): Name of instance, used in plugins
        config (dict): Full configuration, as recorded onto objectSet.

    """
    def __hash__(self):
        """Instances are distinguished solely by their name

        This is in contrast to Python sets in general which are mutable
        and can thus not be part of another collection, such as lists
        or other sets. Since we're collecting Instances within Context
        they must be collectible and identifying them by name seems
        appropriate.

        """

        return hash(self.name)

    def __repr__(self):
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __str__(self):
        return str(self.name)

    def __init__(self, name):
        super(Instance, self).__init__()
        self.name = name
        self.config = dict()


def current_host():
    """Return currently active host

    When running Publish from within a host, this function determines
    which host is running and returns the equivalent keyword.

    Example:
        >> # Running within Autodesk Maya
        >> host()
        'maya'
        >> # Running within Sidefx Houdini
        >> current_host()
        'houdini'

    """

    executable = os.path.basename(sys.executable)

    if 'python' in executable:
        # Running from standalone Python
        return 'python'

    if 'maya' in executable:
        # Maya is distinguished by looking at the currently running
        # executable of the Python interpreter. It will be something
        # like: "maya.exe" or "mayapy.exe"; without suffix for
        # posix platforms.
        return 'maya'

    raise ValueError("Could not determine host")


def register_plugin_path(path):
    """Plug-ins are looked up at run-time from directories registered here

    To register a new directory, run this command along with the absolute
    path to where you're plug-ins are located.

    Example:
        >> my_plugins = '/home/marcus/publish_plugins'
        >> register_plugin_path(my_plugins)

    """

    if os.path.isdir(path):
        registered_paths.add(path)
    else:
        raise OSError("{0} does not exist".format(path))


def deregister_plugin_path(path):
    """Remove a registered_paths path

    Raises:
        KeyError if `path` isn't registered

    """

    registered_paths.remove(path)


def deregister_all():
    """Mainly used in tests"""
    registered_paths.clear()


def discover(type=None, regex=None, context=None):
    """Find plugins within registered_paths plugin-paths

    Arguments:
        type (str): Only return plugins of specified type
            E.g. validators, extractors. In None is
            specified, return all plugins.
        regex (str): Limit results to those matching `regex`
            Mathching is done on classes, as opposed to
            filenames due to a file possibly hosting
            multiple plugins.
        context (Context): Only return plugins compatible
            with specified context.

    """

    if type is not None:
        types = [type]
    else:
        # If no type is specified,
        # discover all plugins
        types = patterns.keys()

    plugins = list()
    for type in types:
        plugins.extend(_discover_type(type=type,
                                      regex=regex))

    return plugins


def plugins_by_instance(plugins, instance):
    """Yield compatible plugins `plugins` to instance `instance`

    Arguments:
        instance (Instance): Instance with which to filter against
        plugins (list): List of plugins

    Returns:
        List of non-instantiated plugins.

    """

    for plugin in plugins:
        if instance.config.get('family') not in plugin.families:
            continue

        if instance.config.get('host') not in plugin.hosts:
            continue

        yield plugin


def instances_by_plugin(instances, plugin):
    """Yield compatible instances `instances` to context `context`

    Arguments:
        context (Context): Context with which to yield compatible instances

    Yields:
        instance (Instance): Compatible instance

    """

    for instance in instances:
        if instance.config.get('family') in plugin.families:
            yield instance


def _discover_type(type, regex=None):
    """Return plugins of type `type`

    Helper method for the above function :func:discover()

    """

    try:
        plugins = set()

        paths = list(registered_paths)

        # Accept paths added via Python and
        # paths via environment variable.
        env_var = publish.config.paths_environment_variable
        env_val = os.environ.get(env_var)
        if env_val:
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
                            if issubclass(obj, publish.backend.plugin.Filter):
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
