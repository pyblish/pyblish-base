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
import abc
import time
import shutil
import logging
import inspect
import warnings
import importlib
import traceback

# Local library
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin


__all__ = ['Plugin',
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
    'validators': pyblish.backend.config.validators_regex,
    'extractors': pyblish.backend.config.extractors_regex,
    'selectors': pyblish.backend.config.selectors_regex,
    'conforms': pyblish.backend.config.conforms_regex
}

registered_paths = list()
registered_modules = list()

log = logging.getLogger('pyblish.backend.plugin')


class Plugin(object):
    """Abstract base-class for plugins

    Attributes:
        hosts: Hosts compatible with plugin
        version: Current version of plugin

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

    def process_all(self, context):
        """Convenience method of the above :meth:process"""
        for instance, error in self.process(context):
            if error is not None:
                raise error


class Selector(Plugin):
    """Parse a given working scene for available Instances"""


class Validator(Plugin):
    """Validate/check/test individual instance for correctness.

    Raises exception upon failure.

    """

    families = list()

    def fix(self):
        """Optional auto-fix for when validation fails"""


class Extractor(Plugin):
    """Physically separate Instance from Host into corresponding Resources

    Yields:
        (Instance, Exception): Output path and exception

    """

    families = list()

    def commit(self, path, instance):
        """Move path `path` relative current workspace

        Arguments:
            path (str): Absolute path to where files are currently located;
                usually a temporary directory.
            instance (Instance): Instance located at `path`

        Todo: Both `path` and `instance` are required for this operation,
            but it doesn't make sense to include both as argument because
            they say pretty much the same thing.

            An alternative is to embed `path` into instance.set_data() prior
            to running `commit()` but the path is ONLY needed during commit
            and will become invalidated afterwards.

            How do we simplify this? Ultimately, the way in which files
            end up in their final destination, relative the working file,
            should be automated and not left up to the user.

        """

        date = time.strftime(pyblish.backend.config.date_format)

        workspace_dir = instance.context.data('workspace_dir')
        if not workspace_dir:
            # Project has not been set. Files will
            # instead end up next to the working file.
            workspace_dir = instance.context.data('current_file')

        published_dir = os.path.join(workspace_dir,
                                     pyblish.backend.config.prefix,
                                     instance.data('family'))

        commit_dir = os.path.join(published_dir, date)

        self.log.info("Moving {0} relative working file..".format(instance))
        shutil.copytree(path, commit_dir)

        self.log.info("Clearing local cache..")
        shutil.rmtree(path)

        return commit_dir


class Conform(Plugin):
    families = list()


class AbstractEntity(set):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._data = dict()

    def data(self, key=None, default=None):
        if key is None:
            return self._data

        return self._data.get(key, default)

    def set_data(self, key, value):
        self._data[key] = value

    def remove_data(self, key):
        self._data.pop(key)

    def has_data(self, key):
        return key in self._data


class Context(AbstractEntity):
    """Maintain a collection of Instances"""

    def create_instance(self, name):
        """Convenience method for the following.

        >>> ctx = Context()
        >>> inst = Instance('name', context=ctx)
        >>> ctx.add(inst)

        """

        instance = Instance(name, context=self)
        self.add(instance)
        return instance


class Instance(AbstractEntity):
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

    def __init__(self, name, context=None):
        super(Instance, self).__init__()
        self.name = name
        self.context = context

    def data(self, key=None, default=None):
        """Treat `name` data-member as an override to native property

        If name is a data-member, it will be used wherever a name is requested.
        That way, names may be overridden via data.

        """

        value = super(Instance, self).data(key, default)

        if key == 'name' and value is None:
            return self.name

        return value

    @property
    def config(self):
        warnings.warn("config deprecated, use .data() instead.",
                      DeprecationWarning,
                      stacklevel=2)
        return self._data


def current_host():
    """Return currently active host

    When running Pyblish from within a host, this function determines
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
        >> my_plugins = '/home/marcus/pyblish_plugins'
        >> register_plugin_path(my_plugins)

    """

    if not os.path.isdir(path):
        raise OSError("{0} does not exist".format(path))

    if path in registered_paths:
        return log.warning("Path already registered: {0}".format(path))

    registered_paths.append(path)


def deregister_plugin_path(path):
    """Remove a registered_paths path

    Raises:
        KeyError if `path` isn't registered

    """

    registered_paths.remove(path)


def deregister_all():
    """Mainly used in tests"""
    registered_paths[:] = []


def discover(type=None, regex=None):
    """Find plugins within registered_paths plugin-paths

    Arguments:
        type (str): Only return plugins of specified type
            E.g. validators, extractors. In None is
            specified, return all plugins.
        regex (str): Limit results to those matching `regex`
            Mathching is done on classes, as opposed to
            filenames due to a file possibly hosting
            multiple plugins.

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
    """Return compatible plugins `plugins` to instance `instance`

    Arguments:
        plugins (list): List of plugins
        instance (Instance): Instance with which to compare against

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
        family = instance.data('family')
        host = instance.data('host')

        if hasattr(plugin, 'families') and family not in plugin.families:
            continue

        # Basic accept wildcards
        # Todo: Expand to take partial wildcards e.g. '*Mesh'
        if '*' not in plugin.hosts and host not in plugin.hosts:
            continue

        compatible.append(plugin)

    return compatible


def instances_by_plugin(instances, plugin):
    """Return compatible instances `instances` to plugin `plugin`

    Arguments:
        instances (list): List of instances
        plugin (Plugin): Plugin with which to compare against

    Returns:
        List of compatible instances

    """

    compatible = list()

    for instance in instances:
        if hasattr(plugin, 'families'):
            if instance.data('family') in plugin.families:
                compatible.append(instance)

    return compatible


def _discover_type(type, regex=None):
    """Return plugins of type `type`

    Helper method for the above function :func:discover()

    """

    try:
        plugins = dict()

        paths = list(registered_paths)

        # Accept paths added via Python and
        # paths via environment variable.
        env_var = pyblish.backend.config.paths_environment_variable
        env_val = os.environ.get(env_var)
        if env_val:
            sep = ';' if os.name == 'nt' else ':'
            paths.extend(env_val.split(sep))

        # Paths may point to the same location but be formatted
        # differently. Do a check here.
        discovered_paths = list()

        # Look through each registered path for potential plugins
        for path in paths:
            log.debug("Looking for plugins in {0}".format(path))

            normpath = os.path.normpath(path)
            if normpath in discovered_paths:
                log.warning("Duplicate path being discovered: {0}".format(
                    path))
                continue

            discovered_paths.append(normpath)

            # Look within each directory for available plugins.
            # Plugins are modules which passes the regex test
            # as per regexes provided by config.yaml.
            for fname in os.listdir(path):
                abspath = os.path.join(path, fname)

                if not os.path.isfile(abspath):
                    continue

                mod_name, suffix = os.path.splitext(fname)

                if mod_name in registered_modules:
                    log.warning("Duplicate module name found: "
                                "{dup} found in {mods}".format(
                                    dup=abspath, mods=registered_modules))
                    continue

                try:
                    pattern = patterns[type]
                except KeyError:
                    raise  # Handled below

                # Modules that don't match the regex aren't plugins.
                if not re.match(pattern, fname):
                    continue

                # Try importing the module. If this fails,
                # for whatever reason, log it and move on.
                try:
                    # Create a local copy of sys.path, clear it
                    # and add our plugin path to try and import.
                    # Once done, restore sys.path.
                    sys_path = list(sys.path)
                    sys.path[:] = []

                    sys.path.append(path)
                    module = importlib.import_module(mod_name)

                except (ImportError, IndentationError) as e:
                    log.warning('"{mod}": Skipped ({msg})'.format(
                        mod=mod_name, msg=e))
                    continue

                finally:
                    # Restore sys.path
                    sys.path[:] = sys_path

                for name in dir(module):
                    obj = getattr(module, name)
                # for name, obj in inspect.getmembers(module):
                    # getmembers will return members including attriutes
                    # and eventual functions. We're only interested in
                    # classes.
                    if not inspect.isclass(obj):
                        continue

                    # All plugins must be subclasses of Plugin
                    if not issubclass(obj, Plugin):
                        continue

                    # Finally, check that the plugin hasn't already been
                    # registered. This may indicate that a plugin has
                    # been created with identical name to another plugin.
                    for plugin in plugins:
                        if obj.__name__ == plugin:
                            log.warning(
                                "Comparing {old} - {new} - Duplicate plugin "
                                "found: {cls}".format(
                                    old=obj.__name__,
                                    new=plugin,
                                    cls=obj))

                    if regex is None or re.match(regex, obj.__name__):
                        plugins[obj.__name__] = obj

        return plugins.values()

    except KeyError:
        raise ValueError("Type not recognised: {0}".format(type))


# Register included plugin path
_package_path = pyblish.backend.lib.main_package_path()
_plugins_path = os.path.join(_package_path, 'backend', 'plugins')
_plugins_path = os.path.abspath(_plugins_path)
register_plugin_path(_plugins_path)
