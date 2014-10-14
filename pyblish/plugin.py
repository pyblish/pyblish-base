"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate" and ends with ".py"

Attributes:
    patterns: Regular expressions used for lookup of plugins.
    _registered_paths: List of all _registered_paths plugin-paths

"""

# Standard library
import os
import re
import sys
import shutil
import logging
import inspect
import traceback

# Local library
import pyblish
import pyblish.lib
import pyblish.error

from pyblish.vendor import iscompatible

config = pyblish.Config()


__all__ = ['Plugin',
           'Selector',
           'Validator',
           'Extractor',
           'Conformer',
           'Context',
           'Instance',
           'discover',
           'plugin_paths',
           'registered_paths',
           'environment_paths',
           'configured_paths',
           'register_plugin_path',
           'deregister_plugin_path',
           'deregister_all']

patterns = {
    'validators': config['validators_regex'],
    'extractors': config['extractors_regex'],
    'selectors': config['selectors_regex'],
    'conformers': config['conformers_regex']
}

_registered_paths = list()

log = logging.getLogger('pyblish.plugin')


class Plugins(list):
    """Plug-in manager"""
    def __init__(self, paths=None):
        self.paths = paths or plugin_paths()
        self.discover()

    def discover(self, paths=None):
        self[:] = discover(paths=paths)

    def lookup_paths(self):
        self.paths = plugin_paths()

    def by_order(self, order):
        plugins = list()
        for plugin in self:
            if plugins.order == order:
                plugins.append()
        return plugins

    def by_type(self, type):
        types = {'selector': 0,
                 'validator': 1,
                 'extractor': 2,
                 'conformer': 3}
        plugins = list()
        for plugin in self:
            if plugins.order == types.get(type):
                plugins.append()
        return plugins

    def by_host(self, host):
        plugins = list()
        for plugin in self:
            if "*" in plugin.hosts or current_host() in plugins.hosts:
                plugins.append(plugin)
        return plugins


@pyblish.lib.log
class Plugin(object):
    """Abstract base-class for plugins

    Attributes:
        hosts: Mandatory specifier for which host application
            this plug-in is compatible with.
        version: Mandatory version for forwards-compatibility.
            Pyblish is (currently not) using the version to allow
            for plug-ins incompatible with a particular running
            instance of Pyblish to co-exist alongside compatible
            versions.
        order: Order in which this plug-in is processed. This is
            used internally to control which plug-ins are processed
            before another so as to allow plug-ins to communicate
            with each other. E.g. one plug-in may provide critical
            information to another and so must be allowed to be
            processed first.
        optional: Whether or not plug-in can be skipped by the user.
        requires: Which version of Pyblish is required by this plug-in.
            Plug-ins requiring a version newer than the current version
            will not be loaded. 1.0.8 was when :attr:`Plugin.requires`
            was first introduced.

    """

    hosts = list()       # Hosts compatible with plugin
    version = (0, 0, 0)  # Current version of plugin
    order = None
    optional = False
    requires = "pyblish>=1"

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def process(self, context):
        """Perform processing upon context `context`

        .. note:: If an instance contains the data "publish" and that data is
            `False` the instance will not be processed.

        Injected data during processing:

        - `__is_processed__`: Whether or not the instance was processed
        - `__processed_by__`: Plugins which processed the given instance

        Returns:
            :meth:`process` returns a generator with (instance, error), with
                error defaulted to `None`. Each error is injected with a
                stack-trace of what went wrong, accessible via error.traceback.

        Yields:
            Tuple (Instance, Exception)

        """

        try:
            self.process_context(context)

        except Exception as err:
            self.log.error("Could not process context: {0}".format(context))
            yield None, err

        else:
            compatible_instances = instances_by_plugin(
                instances=context, plugin=self)

            if not compatible_instances:
                yield None, None

            else:
                for instance in compatible_instances:
                    if instance.has_data('publish'):
                        if instance.data('publish', default=True) is False:
                            self.log.info("Skipping %s" % instance)
                            continue

                    elif not config['publish_by_default']:
                        self.log.info("Skipping %s" % instance)
                        continue

                    self.log.info("Processing instance: \"%s\"" % instance)

                    # Inject data
                    processed_by = instance.data('__processed_by__') or list()
                    processed_by.append(type(self))
                    instance.set_data('__processed_by__', processed_by)
                    instance.set_data('__is_processed__', True)

                    try:
                        self.process_instance(instance)
                        err = None

                    except Exception as err:
                        try:
                            _, _, exc_tb = sys.exc_info()
                            err.traceback = traceback.extract_tb(
                                exc_tb)[-1]
                        except:
                            pass

                        # err.traceback = traceback.format_exc()

                    finally:
                        yield instance, err

    def process_context(self, context):
        """Process `context`

        Implement this method in your subclasses whenever you need
        to process the full context. The principal difference here
        is that only one return value is required, exceptions are
        handled gracefully by :meth:`process` above.

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
        """Convenience method of the above :meth:`process`

        Return:
            None

        """

        for instance, error in self.process(context):
            if error is not None:
                raise error


class Selector(Plugin):
    """Parse a given working scene for available Instances"""

    order = 0


class Validator(Plugin):
    """Validate/check/test individual instance for correctness.

    Raises exception upon failure.

    Attributes:
        families: Supported families.

    """

    families = list()
    order = 1


class Extractor(Plugin):
    """Physically separate Instance from Host into corresponding resources

    By convention, an extractor always positions files relative the
    current working file. Use the convenience :meth:`commit` to maintain
    this convention.

    Attributes:
        families: Supported families.

    """

    families = list()
    order = 2

    def compute_commit_directory(self, instance):
        """Return commit directory for `instance`

        The commit directory is derived from a template, located within
        the configuration. The following variables are substituted at
        run-time:

        - pyblish: With absolute path to pyblish package directory
        - prefix: With Config['prefix']
        - date: With date embedded into `instance`
        - family: With instance embedded into `instance`
        - instance: Name of `instance`
        - user: Currently logged on user, as derived from `instance`

        Arguments:
            instance (Instance): Instance for which to compute a directory

        Returns:
            Absolute path to directory as string

        Raises:
            ExtractorError: When data is missing from `instance`

        """

        workspace_dir = instance.context.data('workspace_dir')
        if not workspace_dir:
            # Project has not been set. Files will
            # instead end up next to the working file.
            current_file = instance.context.data('current_file')
            workspace_dir = os.path.dirname(current_file)

        date = instance.context.data('date')

        # This is assumed from default plugins
        assert date

        if not workspace_dir:
            raise pyblish.error.ExtractorError(
                "Could not determine commit directory. "
                "Instance MUST supply either 'current_file' or "
                "'workspace_dir' as data prior to commit")

        # Remove invalid characters from output name
        name = instance.data('name')
        valid_name = pyblish.lib.format_filename(name)
        if name != valid_name:
            self.log.info("Formatting instance name: "
                          "\"%s\" -> \"%s\""
                          % (name, valid_name))
            name = valid_name

        variables = {'pyblish': pyblish.lib.main_package_path(),
                     'prefix': config['prefix'],
                     'date': date,
                     'family': instance.data('family'),
                     'instance': name,
                     'user': instance.data('user')}

        # Restore separators to those native to the current OS
        commit_template = config['commit_template']
        commit_template = commit_template.replace('/', os.sep)

        commit_dir = commit_template.format(**variables)
        commit_dir = os.path.join(workspace_dir, commit_dir)

        return commit_dir

    def commit(self, path, instance):
        """Move path `path` relative current workspace

        Arguments:
            path (str): Absolute path to where files are currently located;
                usually a temporary directory.
            instance (Instance): Instance located at `path`

        """

        commit_dir = self.compute_commit_directory(instance=instance)

        self.log.info("Moving \"%s\" relative working file.." % instance)

        if os.path.isdir(commit_dir):
            self.log.info("Existing directory found, merging..")
            for fname in os.listdir(path):
                abspath = os.path.join(path, fname)
                commit_path = os.path.join(commit_dir, fname)
                shutil.copy(abspath, commit_path)
        else:
            self.log.info("No existing directory found, creating..")
            shutil.copytree(path, commit_dir)

        # Persist path of commit within instance
        instance.set_data('commit_dir', value=commit_dir)

        return commit_dir


class Conformer(Plugin):
    """Integrates publishes into a pipeline

    Attributes:
        families: Supported families.

    """

    families = list()
    order = 3


class AbstractEntity(list):
    """Superclass for Context and Instance"""

    def __init__(self):
        self._data = dict()

    def add(self, other):
        """Add member to self

        This is to mimic the interface of set()

        """

        if not other in self:
            return self.append(other)

    def remove(self, other):
        """Remove member from self

        This is to mimic the interface of set()

        """

        index = self.index(other)
        return self.pop(index)

    def data(self, key=None, default=None):
        """Return data from `key`

        Arguments:
            key (str): Name of data to return
            default (object): Optional, value returned if `name`
                does not exist

        """

        if key is None:
            return self._data.copy()

        return self._data.get(key, default)

    def set_data(self, key, value):
        """Modify/insert data into entity

        Arguments:
            key (str): Name of data to add
            value (object): Value of data to add

        """

        self._data[key] = value

    def remove_data(self, key):
        """Remove data from entity

        Arguments;
            key (str): Name of data to remove

        """

        self._data.pop(key)

    def has_data(self, key):
        """Check if entity has key

        Arguments:
            key (str): Key to check

        Return:
            True if it exists, False otherwise

        """

        return key in self._data


class Context(AbstractEntity):
    """Maintain a collection of Instances

    .. note:: Context is a singleton.

    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Context, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def delete(cls):
        """Force re-instantiation of context"""
        cls._instance = None

    def create_instance(self, name):
        """Convenience method of the following.

        >>> ctx = Context()
        >>> inst = Instance('name', parent=ctx)
        >>> ctx.add(inst)

        Example:
            >>> ctx = Context()
            >>> inst = ctx.create_instance(name='Name')

        """

        instance = Instance(name, parent=self)
        return instance


@pyblish.lib.log
class Instance(AbstractEntity):
    """An in-memory representation of one or more files

    Examples include rigs, models.

    Arguments:
        name (str): Name of instance, typically used during
            extraction as name of resulting files.
        parent (AbstractEntity): Optional parent. This is
            supplied automatically when creating instances with
            :class:`Context.create_instance()`.

    Attributes:
        name (str): Name of instance, used in plugins
        parent (AbstractEntity): Optional parent of instance

    """

    def __eq__(self, other):
        return self.name == getattr(other, 'name', None)

    def __ne__(self, other):
        return self.name != getattr(other, 'name', None)

    def __repr__(self):
        return u"%s.%s('%s')" % (__name__, type(self).__name__, self)

    def __str__(self):
        return self.name

    def __init__(self, name, parent=None):
        super(Instance, self).__init__()
        assert isinstance(name, basestring)
        assert parent is None or isinstance(parent, AbstractEntity)
        self.name = name
        self.parent = parent

        if parent is not None:
            parent.add(self)

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


def current_host():
    """Return currently active host

    When running Pyblish from within a host, this function determines
    which host is running and returns the equivalent keyword.

    Example:
        >> # Running within Autodesk Maya
        >> current_host()
        'maya'
        >> # Running within Sidefx Houdini
        >> current_host()
        'houdini'

    """

    executable = os.path.basename(sys.executable).lower()

    if 'python' in executable:
        # Running from standalone Python
        return 'python'

    if 'maya' in executable:
        # Maya is distinguished by looking at the currently running
        # executable of the Python interpreter. It will be something
        # like: "maya.exe" or "mayapy.exe"; without suffix for
        # posix platforms.
        return 'maya'

    if 'nuke' in executable:
        # Nuke typically includes a version number, e.g. Nuke8.0.exe
        # and mixed-case letters.
        return 'nuke'

    # ..note:: The following are guesses, feel free to correct

    if 'modo' in executable:
        return 'modo'

    if 'houdini' in executable:
        return 'houdini'

    raise ValueError("Could not determine host")


def register_plugin_path(path):
    """Plug-ins are looked up at run-time from directories registered here

    To register a new directory, run this command along with the absolute
    path to where you're plug-ins are located.

    Example:
        >>> import os
        >>> my_plugins = os.path.expanduser('~')
        >>> register_plugin_path(my_plugins)
        >>> deregister_plugin_path(my_plugins)

    """

    processed_path = _post_process_path(path)

    if processed_path in _registered_paths:
        return log.warning("Path already registered: {0}".format(path))

    _registered_paths.append(processed_path)


def deregister_plugin_path(path):
    """Remove a _registered_paths path

    Raises:
        KeyError if `path` isn't registered

    """

    _registered_paths.remove(path)


def deregister_all():
    """Mainly used in tests"""
    _registered_paths[:] = []


def _post_process_path(path):
    """Before using any incoming path, process it"""
    return os.path.abspath(path)


def registered_paths():
    """Return paths added via registration"""
    log.debug("Registered paths: %s" % _registered_paths)
    return _registered_paths


def configured_paths():
    """Return paths added via configuration"""
    paths = list()

    for path_template in config['paths']:
        variables = {'pyblish': pyblish.lib.main_package_path()}

        plugin_path = path_template.format(**variables)

        # Ensure path is absolute
        plugin_path = _post_process_path(plugin_path)
        paths.append(plugin_path)

        log.debug("Appending path from config: %s" % plugin_path)

    return paths


def environment_paths():
    """Return paths added via environment variable"""

    paths = list()

    env_var = config['paths_environment_variable']
    env_val = os.environ.get(env_var)
    if env_val:
        env_paths = env_val.split(os.pathsep)
        for path in env_paths:
            plugin_path = _post_process_path(path)
            paths.append(plugin_path)

        log.debug("Paths from environment: %s" % env_paths)

    return paths


def plugin_paths():
    """Collect paths from all sources.

    This function looks at the three potential sources of paths
    and returns a list with all of them together.

    The sources are:

    - Registered paths using :func:`register_plugin_path`,
    - Paths from the environment variable `PYBLISHPLUGINPATH`
    - Paths from configuration

    Returns:
        list of paths in which plugins may be locat

    """

    paths = list()

    # Accept registered paths.
    for path in registered_paths() + configured_paths() + environment_paths():
        processed_path = _post_process_path(path)
        if processed_path in paths:
            continue
        paths.append(processed_path)

    return paths


def discover(type=None, regex=None, paths=None):
    """Find plugins within exposed plugin-paths

    Arguments:
        type (str, optional): Only return plugins of specified type
            E.g. validators, extractors. In None is specified, return
            all plugins. Available options are "selectors", validators",
            "extractors", "conformers".
        regex (str, optional): Limit results to those matching `regex`.
            Matching is done on classes, as opposed to
            filenames, due to a file possibly hosting
            multiple plugins.
        paths (list, optional): Paths to discover plug-ins from.
            If no paths are provided, all paths are searched.

    """

    if paths is None:
        paths = plugin_paths()

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
                                          paths=paths,
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
            elif '*' in plugin.families:
                compatible.append(instance)

    return compatible


def _discover_type(type, paths, regex=None):
    """Return plugins of type `type`

    Helper method for the above function :func:discover()

    Raises:
        KeyError when `type` is unrecognised.

    """

    plugins = dict()

    # Paths may point to the same location but be formatted
    # differently. Do a check here.
    discovered_paths = list()

    try:
        pattern = patterns[type]
    except KeyError:
        raise  # Handled by :func:discover()

    # Look through each registered path for potential plugins
    for path in paths:
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

            # Modules that don't match the regex aren't plugins.
            if not re.match(pattern, fname):
                continue

            # Try importing the module. If this fails,
            # for whatever reason, log it and move on.
            try:
                sys.path.insert(0, path)
                module = pyblish.lib.import_module(mod_name)
                reload(module)

            except Exception as err:
                log.warning('Module: "{mod}" skipped ({msg})'.format(
                    mod=mod_name, msg=err))
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

                if not _iscompatible(obj):
                    log.warning(
                        "Plug-in %s not compatible with this version "
                        "(%s) of Pyblish." % (obj, pyblish.__version__))
                    continue

                # Only include plug-ins compatible
                # with the currently running host.
                if not any(["*" in obj.hosts, current_host() in obj.hosts]):
                    continue

                # Finally, check that the plugin hasn't already been
                # registered. This may indicate that a plugin has
                # been created with identical name to another plugin.
                if obj.__name__ in plugins:
                    log.warning(
                        "Duplicate plugin "
                        "found: {cls}".format(cls=obj))
                    continue

                if regex is None or re.match(regex, obj.__name__):
                    plugins[obj.__name__] = obj

    return plugins.values()


def _iscompatible(plugin):
    """Lookup compatibility between plug-in and current version of Pyblish

    Arguments:
        plugin (Plugin): Plug-in to test against

    """

    return iscompatible.iscompatible(
        requirements=plugin.requires, version=pyblish.version_info)


def _isvalid(plugin):
    """Validate plugin"""

    if plugin.order is None:
        log.error("Plug-in must have an order")
        return False

    if not isinstance(plugin.requires, basestring):
        log.error("Plug-in requires must be of type string")
        return False

    # Helper functions
    def has_families(_plugin):
        if not getattr(_plugin, 'families'):
            log.error("%s: Plug-in not valid, missing families.", _plugin)
            return False
        return True

    def has_hosts(_plugin):
        if not getattr(_plugin, 'hosts'):
            log.error("%s: Plug-in not valid, missing hosts.", _plugin)
            return False
        return True

    # Validations
    if issubclass(plugin, Selector):
        return has_hosts(plugin)

    elif issubclass(plugin, Validator) or issubclass(plugin, Extractor):
        return has_hosts(plugin) and has_families(plugin)

    elif issubclass(plugin, Conformer):
        return has_families(plugin)

    else:
        log.error("%s: Is not a plugin", plugin)
        return False

    return True
