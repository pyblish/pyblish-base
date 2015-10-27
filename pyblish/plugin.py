"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate" and ends with ".py"

Attributes:
    patterns: Regular expressions used for lookup of plugins.

"""

# Standard library
import os
import sys
import types
import logging
import inspect
import warnings
import functools
import contextlib

# Local library
import pyblish
import pyblish.lib
import pyblish.error

from .vendor import yaml
from .vendor import iscompatible


log = logging.getLogger("pyblish.plugin")


class Provider(object):
    """Dependency provider

    This object is given a series of "services" that it then distributes
    to a passed function based on the function's argument signature.

    For example, the function func:`myfunc(a, b)` is given the services
    called "a" and "b", given they have previously been added to the provider.

    """

    def __init__(self):
        self._services = dict()

    def get(self, service):
        return self.services.get(service)

    @property
    def services(self):
        services = pyblish._registered_services.copy()
        services.update(self._services)

        # Forwards-compatibility alias
        services["asset"] = services["instance"]

        return services

    @classmethod
    def args(cls, func):
        return [a for a in inspect.getargspec(func)[0]
                if a not in ("self", "cls")]

    def invoke(self, func):
        """Supply function `func` with objects to its signature

        Raises:
            KeyError if an argument asked for is not available

        Returns:
            Result of `func`

        """

        args = self.args(func)
        unavailable = [a for a in args if a not in self.services]

        if unavailable:
            raise KeyError("Unavailable service requested: %s" % unavailable)

        inject = dict((k, v) for k, v in self.services.items()
                      if k in args)

        return func(**inject)

    def inject(self, name, obj):
        self._services[name] = obj


class Config(dict):
    """Wrapper for Pyblish configuration file.

    .. note:: Config is a singleton.

    Attributes:
        CONFIGPATH: Path to configuration, overridable
            via environment variable PYBLISHCONFIGPATH.

    Usage:
        >>> config = Config()
        >>> for key, value in config.iteritems():
        ...     assert key in config
        >>> assert Config() is Config()

    """

    _instance = None

    CONFIGPATH = (os.environ.get("PYBLISHCONFIGPATH") or
                  os.path.join(os.path.dirname(__file__), "config.yaml"))

    log = logging.getLogger("pyblish.Config")

    def __new__(cls, *args, **kwargs):
        """Make Config into a singleton"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(
                cls, *args, **kwargs)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        """Remove all configuration and re-read from disk"""
        self.clear()
        self.load()

        # Deprecated and undocumented variables
        self.update({
            "validators_regex": "^validate_.*\.py$",
            "extractors_regex": "^extract_.*\.py$",
            "selectors_regex": "^select_.*\.py$",
            "conformers_regex": "^conform_.*\.py$",
            "collectors_regex": "^collect_.*\.py$",
            "integrators_regex": "^integrate_.*\.py$",
            "commit_template": "{prefix}/{date}/{family}/{instance}",
            "publish_by_default": True,
            "prefix": "published",
            "identifier": "publishable"
        })

    def load(self):
        """Load default configuration from package dir"""
        with open(self.CONFIGPATH, "r") as f:
            loaded_data = yaml.load(f)

        for key, value in loaded_data.iteritems():
            self[key] = value

        return True


def evaluate_pre11(plugin):
    """Determine whether the plug-in is pre-1.1"""
    plugin.__pre11__ = False

    if hasattr(plugin, "process_context"):
        plugin.__pre11__ = True
        plugin.process = plugin.process_context
        del(plugin.process_context)

    if hasattr(plugin, "process_instance"):
        plugin.__pre11__ = True
        plugin.process = plugin.process_instance
        del(plugin.process_instance)

    # Repair is deprecated
    if hasattr(plugin, "repair_context"):
        plugin.__pre11__ = True
        plugin.repair = plugin.repair_context
        del(plugin.repair_context)

    if hasattr(plugin, "repair_instance"):
        plugin.__pre11__ = True
        plugin.repair = plugin.repair_instance
        del(plugin.repair_instance)


def evaluate_enabledness(plugin):
    """Deterimine whether the plug-in supports Context/Instance"""
    plugin.__contextEnabled__ = False
    plugin.__instanceEnabled__ = False

    args_ = inspect.getargspec(plugin.process).args

    if "instance" in args_:
        plugin.__instanceEnabled__ = True

    if "context" in args_:
        plugin.__contextEnabled__ = True

    # Forwards-compatibility with asset
    if "asset" in args_:
        plugin.__instanceEnabled__ = True


def append_logger(plugin):
    """Append logger to plugin

    The logger will include a plug-in's final name, as defined
    by the subclasser. For example, if a plug-in is defined, subclassing
    :class:`Plugin`, it's given name will be present in log records.

    """

    module = plugin.__module__
    name = plugin.__name__

    # Package name appended, for filtering of LogRecord instances
    logname = "pyblish.%s.%s" % (module, name)
    plugin.log = logging.getLogger(logname)
    plugin.log.setLevel(logging.DEBUG)

    # All messages are handled by root-logger
    plugin.log.propagate = True


class MetaPlugin(type):
    """Rewrite plug-ins written prior to 1.1

    ..warning:: In case of plug-ins written prior to 1.1,
        that also process both instance and context,
        only the instance process will remain available.

    """

    def __init__(cls, *args, **kwargs):
        append_logger(cls)
        evaluate_pre11(cls)
        evaluate_enabledness(cls)
        return super(MetaPlugin, cls).__init__(*args, **kwargs)


@pyblish.lib.log
class Plugin(object):
    """Base-class for plugins

    Attributes:
        hosts: Optionally limit a plug-in to one or more hosts
        families: Optionally limit a plug-in to one or more families
        label: Printed name of plug-in
        active: Whether or not to use plug-in during processing
        version: Optional version for forwards-compatibility.
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
        actions: Actions associated to this plug-in

    """

    __metaclass__ = MetaPlugin

    hosts = ["*"]
    families = ["*"]
    label = None
    active = True
    version = (0, 0, 0)
    order = -1
    optional = False
    requires = "pyblish>=1"
    actions = []

    id = pyblish.lib.classproperty(lambda cls: cls.__name__)

    def __str__(self):
        return self.label or type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def process(self):
        """Primary processing method

        This method is called whenever your plug-in is invoked
        and is injected with object relative to it's signature.

        E.g. process(self, context, instance) will have the current
        context and instance injected into it at run-time.

        Available objects:
            - context
            - instance
            - user
            - time

        Raises:
            Any error

        """

        pass

    def repair(self):
        """DEPRECATED"""
        pass


class Collector(Plugin):
    """Parse a given working scene for available Instances"""

    order = 0


class Validator(Plugin):
    """Validate/check/test individual instance for correctness."""

    order = 1


class Extractor(Plugin):
    """Physically separate Instance from Host into corresponding resources"""

    order = 2


class Integrator(Plugin):
    """Integrates publishes into a pipeline"""

    order = 3


# Backwards-compatibility aliases
Selector = Collector
Conformer = Integrator


class MetaAction(type):
    """Inject additional metadata into Action"""

    def __init__(cls, *args, **kwargs):
        cls.__error__ = None
        if cls.on not in ("all",
                          "processed",
                          "failed",
                          "succeeded"):
            cls.__error__ = (
                "Action had an unrecognised value "
                "for `on`: \"%s\"" % cls.on
            )

        return super(MetaAction, cls).__init__(*args, **kwargs)


@pyblish.lib.log
class Action(object):
    """User-supplied interactive action

    Subclass this class and append to Plugin.actions in order
    to provide your users with optional, context sensitive
    functionality.

    Attributes:
        label: Optional label to display in place of class name.
        active: Whether or not to allow execution of action.
        on: When to enable this action; available options are:
            - "all": Always available (default).
            - "processed": The plug-in has been processed
            - "succeeded": The plug-in has been processed, and succeeded
            - "failed": The plug-in has been processed, and failed
        icon: Name, relative path or absolute path to image for
            use as an icon of this action. For relative paths,
            the current working directory of the host is used and
            names represent icons available via Awesome Icons.
            fortawesome.github.io/Font-Awesome/icons/

    """

    __metaclass__ = MetaAction
    __type__ = "action"

    label = None
    active = True
    on = "all"
    icon = None

    id = pyblish.lib.classproperty(lambda cls: cls.__name__)

    def __str__(self):
        return self.label or type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def process(self):
        pass


class Separator(Action):
    __type__ = "separator"


def Category(label):
    return type("Category", (Action,), {"label": label,
                                        "__type__": "category"})


@contextlib.contextmanager
def logger(handler):
    """Listen in on the global logger

    Arguments:
        handler (Handler): Custom handler with which to use
            to listen for log messages

    """

    l = logging.getLogger()
    old_level = l.level

    l.addHandler(handler)
    l.setLevel(logging.DEBUG)

    try:
        yield
    finally:
        l.removeHandler(handler)
        l.setLevel(old_level)


def process(plugin, context, instance=None, action=None):
    """Produce a single result from a Plug-in

    Arguments:
        plugin(Plugin): Uninstantiated plug-in class
        context(Context): The current Context
        instance(Instance, optional): Instance to process
        action(str): Id of action to process, in place of plug-in.

    Returns:
        Dictionary of result

    """

    import time

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "action": action,
        "error": None,
        "records": list(),
        "duration": None,
    }

    if not action:
        runner = plugin().process
    else:
        actions = dict((a.id, a) for a in plugin.actions)
        action = actions[action] if action else None
        runner = action().process

    records = list()
    handler = pyblish.lib.MessageHandler(records)

    provider = pyblish.plugin.Provider()
    provider.inject("plugin", plugin)
    provider.inject("context", context)
    provider.inject("instance", instance)

    __start = time.time()

    try:
        with logger(handler):
            provider.invoke(runner)
            result["success"] = True
    except Exception as error:
        pyblish.lib.extract_traceback(error)
        result["error"] = error

    __end = time.time()

    for record in records:
        result["records"].append(record)

    result["duration"] = (__end - __start) * 1000  # ms

    if "results" not in context.data:
        context.data["results"] = list()

    context.data["results"].append(result)

    # Backwards compatibility
    result["asset"] = instance  # Deprecated key

    return result


def repair(plugin, context, instance=None):
    """Produce single result from repairing"""

    import time

    if "results" not in context.data:
        context.data["results"] = list()

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "error": None,
        "records": list(),
        "duration": None
    }

    plugin = plugin()

    records = list()
    handler = pyblish.lib.MessageHandler(records)

    provider = pyblish.plugin.Provider()
    provider.inject("context", context)
    provider.inject("instance", instance)

    __start = time.time()

    try:
        with logger(handler):
            provider.invoke(plugin.repair)
            result["success"] = True
    except Exception as error:
        pyblish.lib.extract_traceback(error)
        result["error"] = error

    __end = time.time()

    for record in records:
        result["records"].append(record)

    result["duration"] = (__end - __start) * 1000  # ms

    context.data["results"].append(result)

    return result


class _Dict(dict):
    """Temporary object during transition from set_data to data dictionary"""
    def __init__(self, parent):
        self._parent = parent

    def __call__(self, key=None, default=None):
        if key is None:
            return self.copy()

        if key == "name":
            default = self._parent.name

        return self.get(key, default)


def deprecated(func):
    """Deprecation decorator

    Attach this to deprecated functions or methods.

    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.version_info >= (2, 7):
            warnings.warn_explicit(
                "Call to deprecated function {}.".format(func.__name__),
                category=DeprecationWarning,
                filename=func.func_code.co_filename,
                lineno=func.func_code.co_firstlineno + 1)
        return func(*args, **kwargs)
    return wrapper


class AbstractEntity(list):
    """Superclass for Context and Instance"""

    def __init__(self):
        self.data = _Dict(self)

    @deprecated
    def add(self, other):
        """DEPRECATED - USE .append

        Add member to self

        This is to mimic the interface of set()

        """

        return self.append(other)

    @deprecated
    def remove(self, other):
        """DEPRECATED - USE .pop

        Remove member from self

        This is to mimic the interface of set()

        """

        index = self.index(other)
        return self.pop(index)


class Context(AbstractEntity):
    """Maintain a collection of Instances"""

    id = property(lambda self: "Context")

    def __contains__(self, key):
        """Support both Instance objects and `id` strings

        Example:
            >>> context = Context()
            >>> instance = context.create_instance("MyInstance")
            >>> "MyInstance" in context
            True
            >>> instance in context
            True
            >>> "NotExists" in context
            False

        """

        try:
            key = key.id
        except:
            pass

        return key in [c.id for c in self]

    def create_instance(self, name, **kwargs):
        """Convenience method of the following.

        >>> ctx = Context()
        >>> inst = Instance("name", parent=ctx)

        Example:
            >>> ctx = Context()
            >>> inst = ctx.create_instance(name="Name")

        """

        instance = Instance(name, parent=self)
        instance.data.update(kwargs)
        return instance

    def __getitem__(self, item):
        """Enable support for dict-like getting of children by id

        Example:
            >>> context = Context()
            >>> instance = context.create_instance("MyInstance")
            >>> assert context["MyInstance"].name == "MyInstance"
            >>> assert context[0].name == "MyInstance"
            >>> assert context.get("MyInstance").name == "MyInstance"

        """

        if isinstance(item, int):
            return super(Context, self).__getitem__(item)
        try:
            return next(c for c in self if c.id == item)
        except StopIteration:
            raise KeyError("%s not in list" % item)

    def get(self, key, default=None):
        try:
            return next(c for c in self if c.id == key)
        except StopIteration:
            return default

    @deprecated
    def create_asset(self, *args, **kwargs):
        return self.create_instance(*args, **kwargs)

    @deprecated
    def add(self, other):
        return super(Context, self).append(other)


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
        id (str): Unique identifier of instance
        name (str): Name of instance
        parent (AbstractEntity): Optional parent of instance

    """

    id = property(lambda self: self.name)

    def __eq__(self, other):
        return self.id == getattr(other, "id", None)

    def __ne__(self, other):
        return self.id != getattr(other, "id", None)

    def __repr__(self):
        return u"%s.%s(\"%s\")" % (__name__, type(self).__name__, self)

    def __str__(self):
        return self.name

    def __init__(self, name, parent=None):
        super(Instance, self).__init__()
        assert isinstance(name, basestring)
        assert parent is None or isinstance(parent, AbstractEntity)
        self.name = name
        self.parent = parent

        self.data["name"] = name
        self.data["family"] = "default"

        if parent is not None:
            parent.append(self)

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


# Forwards-compatibility alias
Asset = Instance


def current_host():
    """Return host last registered thru `register_host()`

    When running Pyblish from within a host, this function determines
    which host is running and returns the equivalent keyword.

    Example:
        >> # Running within Autodesk Maya
        >> current_host()
        "maya"
        >> # Running within Sidefx Houdini
        >> current_host()
        "houdini"
        >> # Running from an unknown software
        >> current_host()
        "unknown"

    """

    return pyblish._registered_hosts[-1] or "unknown"


def register_plugin(plugin):
    """Register a new plug-in

    Arguments:
        plugin (Plugin): Plug-in to register

    Raises:
        TypeError if `plugin` is not callable

    """

    if not hasattr(plugin, "__call__"):
        raise TypeError("Plug-in must be callable "
                        "returning an instance of a class")

    if not plugin_is_valid(plugin):
        raise TypeError("Plug-in invalid: %s", plugin)

    if not version_is_compatible(plugin):
        raise TypeError(
            "Plug-in %s not compatible with "
            "this version (%s) of Pyblish." % (
                plugin, pyblish.__version__))

    if not host_is_compatible(plugin):
        raise TypeError("Plug-in %s is not compatible "
                        "with this host" % plugin)

    pyblish._registered_plugins[plugin.__name__] = plugin


def deregister_plugin(plugin):
    """De-register an existing plug-in

    Arguments:
        plugin (Plugin): Existing plug-in to de-register

    """

    pyblish._registered_plugins.pop(plugin.__name__)


def deregister_all_plugins():
    """De-register all plug-ins"""
    pyblish._registered_plugins.clear()


def register_service(name, obj):
    """Register a new service

    Arguments:
        name (str): Name of service
        obj (object): Any object

    """

    pyblish._registered_services[name] = obj


def deregister_service(name):
    """De-register an existing service by name

    Arguments:
        name (str): Name of service

    """

    pyblish._registered_services.pop(name)


def deregister_all_services():
    """De-register all existing services"""
    pyblish._registered_services.clear()


def registered_services():
    """Return the currently registered services as a dictionary

    .. note:: This returns a copy of the registered paths
        and can therefore not be modified directly.

    """

    return pyblish._registered_services.copy()


def register_plugin_path(path):
    """Plug-ins are looked up at run-time from directories registered here

    To register a new directory, run this command along with the absolute
    path to where you"re plug-ins are located.

    Example:
        >>> import os
        >>> my_plugins = "/server/plugins"
        >>> register_plugin_path(my_plugins)
        '/server/plugins'

    Returns:
        Actual path added, including any post-processing

    """

    if path in pyblish._registered_paths:
        return log.warning("Path already registered: {0}".format(path))

    pyblish._registered_paths.append(path)

    return path


def deregister_plugin_path(path):
    """Remove a pyblish._registered_paths path

    Raises:
        KeyError if `path` isn't registered

    """

    pyblish._registered_paths.remove(path)


def deregister_all_paths():
    """Mainly used in tests"""
    pyblish._registered_paths[:] = []


def registered_paths():
    """Return paths added via registration

    ..note:: This returns a copy of the registered paths
        and can therefore not be modified directly.

    """

    return list(pyblish._registered_paths)


def registered_plugins():
    """Return plug-ins added via :func:`register_plugin`

    .. note:: This returns a copy of the registered plug-ins
        and can therefore not be modified directly

    """

    return pyblish._registered_plugins.values()


def register_host(host):
    """Register a new host

    Registered hosts are used to filter discovered
    plug-ins by host.

    Example:
        >>> register_host("My Host")
        >>> "My Host" in registered_hosts()
        True

    """

    if host not in pyblish._registered_hosts:
        pyblish._registered_hosts.append(host)


def deregister_host(host, quiet=False):
    """Remove an already registered host

    Arguments:
        host (str): Name of host
        quiet (bool): Whether to raise an exception
            when attempting to remove a host that is
            not already registered.

    """

    try:
        pyblish._registered_hosts.remove(host)
    except Exception as e:
        if not quiet:
            raise e


def deregister_all_hosts():
    pyblish._registered_hosts[:] = []


def registered_hosts():
    """Return the currently registered hosts"""
    return list(pyblish._registered_hosts)


def configured_paths():
    """Return paths added via configuration"""
    paths = list()
    config = Config()

    for path_template in config["paths"]:
        variables = {"pyblish": pyblish.lib.main_package_path()}

        plugin_path = path_template.format(**variables)

        paths.append(plugin_path)

    return paths


def environment_paths():
    """Return paths added via environment variable"""

    paths = list()
    config = Config()

    env_var = config["paths_environment_variable"]
    env_val = os.environ.get(env_var)
    if env_val:
        env_paths = env_val.split(os.pathsep)
        for path in env_paths:
            paths.append(path)

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

    for path in registered_paths() + configured_paths() + environment_paths():
        if path in paths:
            continue
        paths.append(path)

    return paths


def discover(type=None, regex=None, paths=None):
    """Find and return available plug-ins

    This function looks for files within paths registered via
    :func:`register_plugin_path` and those added to `PYBLISHPLUGINPATH`.

    It determines *type* - :class:`Selector`, :class:`Validator`,
    :class:`Extractor` or :class:`Conform` - based on whether it
    matches it's corresponding regular expression; e.g.
    "$validator_*^" for plug-ins of type Validator.

    Arguments:
        type (str, optional): !DEPRECATED! Only return plugins of
            specified type. E.g. validators, extractors. In None is specified,
            return all plugins. Available options are "selectors", validators",
            "extractors", "conformers", "collectors" and "integrators".
        regex (str, optional): Limit results to those matching `regex`.
            Matching is done on classes, as opposed to
            filenames, due to a file possibly hosting
            multiple plugins.
        paths (list, optional): Paths to discover plug-ins from.
            If no paths are provided, all paths are searched.

    """

    if type is not None:
        warnings.warn("type argument has been deprecated and does nothing")

    if regex is not None:
        warnings.warn("pyblish.plugin.discover(): regex argument "
                      "has been deprecated and does nothing")

    plugins = dict()

    # Include plug-ins from registered paths
    for path in paths or plugin_paths():
        path = os.path.normpath(path)
        if not os.path.isdir(path):
            continue

        for fname in os.listdir(path):
            if fname.startswith("_"):
                continue

            abspath = os.path.join(path, fname)

            if not os.path.isfile(abspath):
                continue

            mod_name, mod_ext = os.path.splitext(fname)

            if not mod_ext == ".py":
                continue

            module = types.ModuleType(mod_name)
            module.__file__ = abspath

            try:
                execfile(abspath, module.__dict__)

                # Store reference to original module, to avoid
                # garbage collection from collecting it's global
                # imports, such as `import os`.
                sys.modules[mod_name] = module

            except Exception as err:
                log.debug("Skipped: \"%s\" (%s)", mod_name, err)
                continue

            for plugin in plugins_from_module(module):
                if plugin.id in plugins:
                    log.debug("Duplicate plug-in found: %s", plugin)
                    continue

                plugins[plugin.id] = plugin

    # Include plug-ins from registration.
    # Directly registered plug-ins take precedence.
    for name, plugin in pyblish._registered_plugins.iteritems():
        if name in plugins:
            log.debug("Duplicate plug-in found: %s", plugin)
            continue
        plugins[name] = plugin

    plugins = plugins.values()
    sort(plugins)  # In-place

    return plugins


def plugins_from_module(module):
    """Return plug-ins from module

    Arguments:
        module (types.ModuleType): Imported module from which to
            parse valid Pyblish plug-ins.

    Returns:
        List of plug-ins, or empty list if none is found.

    """

    plugins = list()

    for name in dir(module):
        if name.startswith("_"):
            continue

        # It could be anything at this point
        obj = getattr(module, name)

        if not inspect.isclass(obj):
            continue

        if not issubclass(obj, Plugin):
            continue

        if not plugin_is_valid(obj):
            log.debug("Plug-in invalid: %s", obj)
            continue

        if not version_is_compatible(obj):
            log.debug("Plug-in %s not compatible with "
                      "this version (%s) of Pyblish." % (
                          obj, pyblish.__version__))
            continue

        if not host_is_compatible(obj):
            continue

        plugins.append(obj)

    return plugins


def plugin_is_valid(plugin):
    """Determine whether or not plug-in `plugin` is valid

    Arguments:
        plugin (Plugin): Plug-in to assess

    """

    if not isinstance(plugin.requires, basestring):
        log.debug("Plug-in requires must be of type string: %s", plugin)
        return False

    if not isinstance(plugin.families, list):
        log.debug(".families must be list of stirngs")
        return False

    if not isinstance(plugin.hosts, list):
        log.debug(".hosts must be list of strings")
        return False

    for family in plugin.families:
        if not isinstance(family, basestring):
            log.debug("Families must be string")
            return False

    for host in plugin.hosts:
        if not isinstance(host, basestring):
            log.debug("Hosts must be string")
            return False

    return True


def version_is_compatible(plugin):
    """Lookup compatibility between plug-in and current version of Pyblish

    Arguments:
        plugin (Plugin): Plug-in to test against

    """

    if not iscompatible.iscompatible(requirements=plugin.requires,
                                     version=pyblish.version_info):
        return False
    return True


def host_is_compatible(plugin):
    """Determine whether plug-in `plugin` is compatible with the current host

    Available hosts are determined by :func:`registered_hosts`.

    Arguments:
        plugin (Plugin): Plug-in to assess.

    """

    if "*" in plugin.hosts:
        return True

    return any(host in plugin.hosts for host in registered_hosts())


def sort(plugins):
    """Sort `plugins` in-place

    Their order is determined by their `order` attribute,
    which defaults to their standard execution order:

        1. Selection
        2. Validation
        3. Extraction
        4. Conform

    *But may be overridden.

    Arguments:
        plugins (list): Plug-ins to sort

    """

    plugins.sort(key=lambda p: p.order)
    return plugins


# Compatibility
#
# The below members represent backwards compatibility
# features, kept separate for maintainability as they
# will no longer be updated and eventually discarded.


def set_data(self, key, value):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Modify/insert data into entity

    Arguments:
        key (str): Name of data to add
        value (object): Value of data to add

    """

    self.data[key] = value


def remove_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Remove data from entity

    Arguments;
        key (str): Name of data to remove

    """

    self.data.pop(key)


def has_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Check if entity has key

    Arguments:
        key (str): Key to check

    Return:
        True if it exists, False otherwise

    """

    return key in self.data


AbstractEntity.set_data = set_data
AbstractEntity.remove_data = remove_data
AbstractEntity.has_data = has_data
