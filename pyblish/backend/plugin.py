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
    registered_modules: All loaded modules. (Used to ensure no module
        ever has the same name as a module already loaded)

"""

# Standard library
import os
import re
import sys
import abc
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


@pyblish.backend.lib.log
class Plugin(object):
    """Abstract base-class for plugins"""

    __metaclass__ = abc.ABCMeta

    hosts = list()       # Hosts compatible with plugin
    version = (0, 0, 0)  # Current version of plugin

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def process(self, context):
        """Perform processing upon context `context`

        Returns:
            Generator, yielding per instance

        Yields:
            Tuple (Instance, Exception)

        """

        debug = self.log.debug
        error = self.log.error

        try:
            self.process_context(context)

        except Exception as err:
            error(traceback.format_exc())
            error("Could not process context: {0}".format(context))
            yield None, err

        else:
            compatible_instances = pyblish.backend.plugin.instances_by_plugin(
                instances=context, plugin=self)

            if not compatible_instances:
                yield None, None

            else:
                for instance in compatible_instances:
                    debug("\t- %s" % instance)

                    try:
                        self.process_instance(instance)
                        err = None
                    except Exception as err:
                        error(traceback.format_exc())
                        error("An exception occured during "
                              "processing of instance {0}".format(
                                  instance))
                    finally:
                        yield instance, err

    def process_context(self, context):
        """Process context `context`

        Implement this method in your subclasses whenever you need
        to process the full context. The principal difference here
        is that only one return value is required, exceptions are
        handled gracefully by :meth:process above.

        Returns:
            None

        Raises:
            Any error

        """

    def process_instance(self, instance):
        """Process individual, compatible instances

        Implement this method in your subclasses to handle processing
        of compatible instances. It is run once per instance and
        distinguishes between instances compatible with the plugin's
        family and host automatically.

        Returns:
            None

        Raises:
            Any error

        """

    def process_all(self, context):
        """Convenience method of the above :meth:process

        Return:
            None

        """

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

        if instance.context.data('current_file') is None:
            raise ValueError("Cannot commit with data 'current_file'")

        workspace_dir = instance.context.data('workspace_dir')
        if not workspace_dir:
            # Project has not been set. Files will
            # instead end up next to the working file.
            current_file = instance.context.data('current_file')
            workspace_dir = os.path.dirname(current_file)

        date = instance.context.data('date')

        # These two are assumed from built-in plugins
        assert date
        assert workspace_dir

        # Commit directory based on template, see config.json
        variables = {'prefix': pyblish.backend.config.prefix,
                     'date': date,
                     'family': instance.data('family'),
                     'instance': instance.data('name'),
                     'user': instance.data('user')}

        # Restore separators to those native to the current OS
        commit_template = pyblish.backend.config.commit_template
        commit_template = commit_template.replace('/', os.sep)

        commit_dir = commit_template.format(**variables)
        commit_dir = os.path.join(workspace_dir, commit_dir)

        self.log.info("Moving {0} relative working file..".format(instance))

        if os.path.isdir(commit_dir):
            self.log.info("Existing directory found, merging..")
            for fname in os.listdir(path):
                abspath = os.path.join(path, fname)
                commit_path = os.path.join(commit_dir, fname)
                shutil.copy(abspath, commit_path)
        else:
            self.log.info("No existing directory found, creating..")
            shutil.copytree(path, commit_dir)

        self.log.info("Clearing local cache..")
        shutil.rmtree(path)

        # Persist path of commit within instance
        instance.set_data('commit_dir', value=commit_dir)

        return commit_dir


class Conform(Plugin):
    families = list()


class AbstractEntity(list):
    __metaclass__ = abc.ABCMeta

    def __repr__(self):
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __str__(self):
        return str([i for i in self])

    def __init__(self):
        self._data = dict()

    def add(self, other):
        if not other in self:
            self.append(other)

    def remove(self, other):
        self.remove(other)

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
        >>> inst = Instance('name', parent=ctx)
        >>> ctx.add(inst)

        """

        instance = Instance(name, parent=self)
        self.add(instance)
        return instance


@pyblish.backend.lib.log
class Instance(AbstractEntity):
    """An individually publishable component within scene

    Examples include rigs, models.

    Attributes:
        name (str): Name of instance, used in plugins
        config (dict): Full configuration, as recorded onto objectSet.

    """

    def __eq__(self, other):
        return str(other) == str(self)

    def __ne__(self, other):
        return str(other) != str(self)

    def __hash__(self):
        """Ensure instance is unique within list

        Example:
            >>> ctx = Context()
            >>> inst1 = Instance(name='inst1')
            >>> inst2 = Instance(name='inst2')
            >>> ctx.add(inst1)
            >>> inst2 in ctx
            False
            >>> ctx.add(inst2)
            >>> inst2 in ctx
            True
            >>> inst_ = Instance(name='inst2')
            >>> inst_ in ctx
            True

        """

        return hash(str(self))

    def __str__(self):
        return str(self.name)

    def __init__(self, name, parent=None):
        super(Instance, self).__init__()
        self.name = name
        self.parent = parent

    @property
    def context(self):
        """Return top-level parent; the context"""
        parent = self.parent
        while parent:
            try:
                parent = parent.parent
            except:
                break
        assert isinstance(parent, Context)
        return parent

    def data(self, key=None, default=None):
        """Treat `name` data-member as an override to native property

        If name is a data-member, it will be used wherever a name is requested.
        That way, names may be overridden via data.

        Example:
            >>> inst = Instance(name='test')
            >>> assert inst.data('name') == 'test'
            >>> inst.set_data('name', 'newname')
            >>> assert inst.data('name') == 'newname'

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
        try:
            plugins.extend(_discover_type(type=type,
                                          regex=regex))
        except KeyError:
            raise ValueError("Type not recognised: {0}".format(type))

    return plugins


def plugins_by_family(plugins, family):
    """Return compatible plugins `plugins` to family `family`

    Arguments:
        plugins (list): List of plugins
        family (str): Family with which to compare against

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
        if hasattr(plugin, 'families') and family not in plugin.families:
            continue

        compatible.append(plugin)

    return compatible


def plugins_by_host(plugins, host):
    """Return compatible plugins `plugins` to host `host`

    Arguments:
        plugins (list): List of plugins
        host (str): Host with which compatible plugins are returned

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
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

    Raises:
        KeyError when `type` is unrecognised.

    """

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
        log.debug("Looking for plugins in: \n%s", path)

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
                # Todo: This isn't fool-proof.
                # By inserting path, we can't be sure whether
                # the module we find is in the added path or
                # in a path previously added.
                sys.path.insert(0, path)
                module = importlib.import_module(mod_name)

            except (ImportError, IndentationError) as e:
                log.warning('"{mod}": Skipped ({msg})'.format(
                    mod=mod_name, msg=e))
                continue

            finally:
                # Restore sys.path
                sys.path.remove(path)

            for name in dir(module):
                obj = getattr(module, name)
                if not inspect.isclass(obj):
                    continue

                # All plugins must be subclasses of Plugin
                if not issubclass(obj, Plugin):
                    continue

                if not _isvalid(obj):
                    continue

                # Finally, check that the plugin hasn't already been
                # registered. This may indicate that a plugin has
                # been created with identical name to another plugin.
                if obj.__name__ in plugins:
                    log.warning(
                        "Duplicate plugin "
                        "found: {cls}".format(cls=obj))

                if regex is None or re.match(regex, obj.__name__):
                    plugins[obj.__name__] = obj

    return plugins.values()


def _isvalid(plugin):
    """Validate plugin"""

    # Helper functions
    def has_families(_plugin):
        if not getattr(_plugin, 'families'):
            log.error("%s: Plugin not valid, missing families.", _plugin)
            return False
        return True

    def has_hosts(_plugin):
        if not getattr(_plugin, 'hosts'):
            log.error("%s: Plugin not valid, missing hosts.", _plugin)
            return False
        return True

    # Validations
    if issubclass(plugin, Selector):
        return has_hosts(plugin)

    elif issubclass(plugin, Validator) or issubclass(plugin, Extractor):
        return has_hosts(plugin) and has_families(plugin)

    elif issubclass(plugin, Conform):
        return has_families(plugin)

    else:
        log.error("%s: Is not a plugin", plugin)
        return False

    return True


# Register included plugins
_package_path = pyblish.backend.lib.main_package_path()
_plugins_path = os.path.join(_package_path, 'backend', 'plugins')
_plugins_path = os.path.abspath(_plugins_path)
register_plugin_path(_plugins_path)
