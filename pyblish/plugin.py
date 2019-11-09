"""Plug-in system

Works similar to how OSs look for executables; i.e. a number of
absolute paths are searched for a given match. The predicate for
executables is whether or not an extension matches a number of
options, such as ".exe" or ".bat".

In this system, the predicate is whether or not a fname starts
with "validate" and ends with ".py"

"""

# Standard library
import os
import sys
import time
import types
import logging
import inspect
import warnings
import contextlib
import uuid

# Local library
from . import (
    __version__,
    version_info,
    _registered_callbacks,
    _registered_services,
    _registered_plugins,
    _registered_hosts,
    _registered_paths,
    _registered_targets,
    _registered_plugin_filters
)

from . import lib
from .vendor import iscompatible, six

log = logging.getLogger("pyblish.plugin")

__metaclass__ = type  # Make all classes new-style

# Matching algorithms
Intersection = 1 << 0
Subset = 1 << 1
Exact = 1 << 2

# Check for duplicate plugin names. This is to preserve backwards compatility.
ALLOW_DUPLICATES = bool(os.getenv("PYBLISH_ALLOW_DUPLICATE_PLUGIN_NAMES"))

# Check for strict data types. This is to preserve backwards compatility
STRICT_DATATYPES = bool(os.getenv("PYBLISH_STRICT_DATATYPES"))

# Check for early adopters.
EARLY_ADOPTER = bool(os.getenv("PYBLISH_EARLY_ADOPTER"))
ALLOW_DUPLICATE_PLUGINS = EARLY_ADOPTER or ALLOW_DUPLICATES
STRICT_DATATYPES = EARLY_ADOPTER or STRICT_DATATYPES


class Provider():
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
        services = _registered_services.copy()
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

    # Backwards-compatibility with asset
    if "asset" in args_:
        plugin.__instanceEnabled__ = True


def append_logger(plugin):
    """Append logger to plugin

    The logger will include a plug-in's final name, as defined
    by the subclasser. For example, if a plug-in is defined, subclassing
    :class:`Plugin`, it's given name will be present in log records.

    """

    name = plugin.__name__

    # Package name appended, for filtering of LogRecord instances
    logname = "pyblish.%s" % name
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

        # Compute once
        cls._id = str(uuid.uuid4())
        cls.id = lib.classproperty(lambda self: self._id)

        return super(MetaPlugin, cls).__init__(*args, **kwargs)


@lib.log
@six.add_metaclass(MetaPlugin)
class Plugin():
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
        id: Unique ID as str
        match: Family matching algorithm - Intersection, Subset or Exact
            Intersection -> set(a).intersection(b)
            Subset       -> set(a).issubset(b)
            Exact        -> a == b

    """

    hosts = ["*"]
    families = ["*"]
    targets = ["default"]
    label = None
    active = True
    version = (0, 0, 0)
    order = -1
    optional = False
    requires = "pyblish>=1"
    actions = []
    id = None  # Defined by metaclass
    match = Intersection  # Default matching algorithm

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


CollectorOrder = 0
ValidatorOrder = 1
ExtractorOrder = 2
IntegratorOrder = 3


def validate_argument_signature(plugin):
    """Ensure plug-in processes either 'instance' or 'context'"""
    if not any(arg in inspect.getargspec(plugin.process).args
               for arg in ("instance", "context")):
        plugin.__invalidSignature__ = True


class ExplicitMetaPlugin(MetaPlugin):
    """Validate explicit plug-ins"""

    def __init__(cls, *args, **kwargs):
        validate_argument_signature(cls)
        return super(ExplicitMetaPlugin, cls).__init__(*args, **kwargs)


@six.add_metaclass(ExplicitMetaPlugin)
class ContextPlugin(Plugin):

    def process(self, context):
        """Primary processing method

        Arguments:
            context (Context): Context with which to process

        """


@six.add_metaclass(MetaPlugin)
class InstancePlugin(Plugin):

    def process(self, instance):
        """Primary processing method

        Arguments:
            instance (Instance): Instance with which to process

        """


class MetaAction(type):
    """Inject additional metadata into Action"""

    def __init__(cls, *args, **kwargs):
        cls._id = str(uuid.uuid4())
        cls.id = lib.classproperty(lambda self: cls._id)

        cls.__error__ = None

        if cls.on not in ("all",
                          "notProcessed",
                          "processed",
                          "failed",
                          "succeeded"):
            cls.__error__ = (
                "Action had an unrecognised value "
                "for `on`: \"%s\"" % cls.on
            )

        return super(MetaAction, cls).__init__(*args, **kwargs)


@lib.log
@six.add_metaclass(MetaAction)
class Action():
    """User-supplied interactive action

    Subclass this class and append to Plugin.actions in order
    to provide your users with optional, context sensitive
    functionality.

    Attributes:
        label: Optional label to display in place of class name.
        active: Whether or not to allow execution of action.
        on: When to enable this action; available options are:
            - "all": Always available (default).
            - "notProcessed": The plug-in has not yet been processed
            - "processed": The plug-in has been processed
            - "succeeded": The plug-in has been processed, and succeeded
            - "failed": The plug-in has been processed, and failed
        icon: Name, relative path or absolute path to image for
            use as an icon of this action. For relative paths,
            the current working directory of the host is used and
            names represent icons available via Awesome Icons.
            fortawesome.github.io/Font-Awesome/icons/

    """

    __type__ = "action"

    label = None
    active = True
    on = "all"
    icon = None

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

    logger = logging.getLogger()
    old_level = logger.level

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        yield
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


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

    if issubclass(plugin, (ContextPlugin, InstancePlugin)):
        result = __explicit_process(plugin, context, instance, action)
    else:
        result = __implicit_process(plugin, context, instance, action)

    lib.emit("pluginProcessed", result=result)
    return result


def __explicit_process(plugin, context, instance=None, action=None):
    """Produce result from explicit plug-in

    This is the primary internal mechanism for producing results
    from the processing of plug-in/instance pairs.

    This mechanism replaces :func:`__implicit_process`.

    """

    if not action and issubclass(plugin, InstancePlugin) and instance is None:
        raise AssertionError("Cannot process an InstancePlugin without an "
                             "instance. This is a bug")

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "action": action,
        "error": None,
        "records": list(),
        "duration": None,
        "progress": 0,
    }

    if not action:
        args = (context if issubclass(plugin, ContextPlugin) else instance,)
        runner = plugin().process
    else:
        actions = dict((a.id, a) for a in plugin.actions)
        assert action in actions, ("%s did not have action: %s. This is a bug"
                                   % (plugin, action))
        action = actions[action]
        args = (context, plugin)
        runner = action().process

    records = list()
    handler = lib.MessageHandler(records)

    __start = time.time()

    try:
        with logger(handler):
            runner(*args)
            result["success"] = True
    except Exception as error:
        # FIXME: This is apparently not very healthy,
        # as it creates a circular reference.
        # http://stackoverflow.com/a/11417308/478949
        lib.emit("pluginFailed", plugin=plugin, context=context,
                 instance=instance, error=error)
        lib.extract_traceback(error, plugin.__module__)
        result["error"] = error
        log.exception(result["error"].formatted_traceback)

    __end = time.time()

    for record in records:
        result["records"].append(record)

    result["duration"] = (__end - __start) * 1000  # ms

    if "results" not in context.data:
        context.data["results"] = list()

    context.data["results"].append(result)

    return result


def __implicit_process(plugin, context, instance=None, action=None):
    """Produce result from implicit plug-in

    This is a fallback mechanism for backwards compatibility.
    An implicit plug-in are those subclassed from Collector,
    Validator, Extractor or Integrator.

    The mechanism which replaces this is :func:`__explicit_process`.

    """

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "action": action,
        "error": None,
        "records": list(),
        "duration": None,
        "progress": 0,
    }

    if not action:
        runner = plugin().process
    else:
        actions = dict((a.id, a) for a in plugin.actions)
        assert action in actions, ("%s did not have action: %s. This is a bug"
                                   % (plugin, action))
        action = actions[action]
        runner = action().process

    records = list()
    handler = lib.MessageHandler(records)

    provider = Provider()
    provider.inject("plugin", plugin)
    provider.inject("context", context)
    provider.inject("instance", instance)

    __start = time.time()

    try:
        with logger(handler):
            provider.invoke(runner)
            result["success"] = True
    except Exception as error:
        lib.emit("pluginFailed", plugin=plugin, context=context,
                 instance=instance, error=error)
        lib.extract_traceback(error, plugin.__module__)
        result["error"] = error
        log.exception(result["error"].formatted_traceback)

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
    handler = lib.MessageHandler(records)

    provider = Provider()
    provider.inject("context", context)
    provider.inject("instance", instance)

    __start = time.time()

    try:
        with logger(handler):
            provider.invoke(plugin.repair)
            result["success"] = True
    except Exception as error:
        lib.extract_traceback(error)
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

    def __setitem__(self, k, v):
        # Backwards incompatible data validation.
        if STRICT_DATATYPES:
            # Validate "publish" data member to always be boolean
            if k == "publish" and not isinstance(v, bool):
                raise TypeError("\"publish\" data member has to be boolean.")

        dict.__setitem__(self, k, v)


class AbstractEntity(list):
    """Superclass for Context and Instance

    Attributes:
        id (str): Unique identifier of instance
        name (str): Name of instance
        data (dict): Data shared between plug-ins
        parent (AbstractEntity): Optional parent of instance

    """

    def __init__(self, name, parent=None):
        assert isinstance(name, six.string_types)
        assert parent is None or isinstance(parent, AbstractEntity)

        # Read-only properties
        self._name = name
        self._data = _Dict(self)
        self._id = str(uuid.uuid4())
        self._parent = parent

        if parent is not None:
            parent.append(self)

    @property
    def id(self):
        return self._id

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data


class Context(AbstractEntity):
    """Maintain a collection of Instances"""

    def __init__(self, name="Context", parent=None):
        super(Context, self).__init__(name, parent)

    def __contains__(self, key):
        """Support both Instance objects and `id` strings

        Example:
            >>> context = Context()
            >>> instance = context.create_instance("MyInstance")
            >>> instance.id in context
            True
            >>> instance in context
            True
            >>> "NotExists" in context
            False

        """

        try:
            key = key.id
        except Exception:
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
            >>> assert context[instance.id].name == "MyInstance"
            >>> assert context[0].name == "MyInstance"

        """

        if isinstance(item, int):
            return super(Context, self).__getitem__(item)
        try:
            return next(c for c in self if c.id == item)
        except StopIteration:
            raise KeyError("%s not in list" % item)

    def get(self, key, default=None):
        """Enable support for dict-like getting of children by id

        Example
            >>> context = Context()
            >>> instance = context.create_instance("MyInstance")
            >>> assert context.get(instance.id).name == "MyInstance"

        """

        return next((c for c in self if c.id == key), default)


@lib.log
class Instance(AbstractEntity):
    """An in-memory representation of one or more files

    Examples include rigs, models.

    Arguments:
        name (str): Name of instance, typically used during
            extraction as name of resulting files.
        parent (AbstractEntity): Optional parent. This is
            supplied automatically when creating instances with
            :class:`Context.create_instance()`.

    """

    def __init__(self, name, parent=None):
        super(Instance, self).__init__(name, parent)
        self._data["family"] = "default"
        self._data["name"] = name

    def __eq__(self, other):
        return self._id == getattr(other, "id", None)

    def __ne__(self, other):
        return self._id != getattr(other, "id", None)

    def __repr__(self):
        return u"%s.%s(\"%s\")" % (__name__, type(self).__name__, self)

    def __str__(self):
        return self._name

    @property
    def context(self):
        """Return top-level parent; the context"""
        parent = self.parent
        while parent.parent:
            try:
                parent = parent.parent
            except Exception:
                break

        assert isinstance(parent, Context), ("Parent was not a Context:"
                                             "%s" % type(parent))

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

    return _registered_hosts[-1] if _registered_hosts else "unknown"


def register_callback(signal, callback):
    """Register a new callback

    Arguments:
        signal (string): Name of signal to register the callback with.
        callback (func): Function to execute when a signal is emitted.

    Raises:
        ValueError if `callback` is not callable.

    """

    if not hasattr(callback, "__call__"):
        raise ValueError("%s is not callable" % callback)

    if signal in _registered_callbacks:
        _registered_callbacks[signal].append(callback)
    else:
        _registered_callbacks[signal] = [callback]


def deregister_callback(signal, callback):
    """Deregister a callback

    Arguments:
        signal (string): Name of signal to deregister the callback with.
        callback (func): Function to execute when a signal is emitted.

    Raises:
        KeyError on missing signal
        ValueError on missing callback
    """

    _registered_callbacks[signal].remove(callback)


def deregister_all_callbacks():
    """Deregisters all callback"""

    _registered_callbacks.clear()


def registered_callbacks():
    """Returns registered callbacks"""

    return _registered_callbacks


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
                plugin, __version__))

    if not host_is_compatible(plugin):

        hosts = registered_hosts()
        required_hosts = plugin.hosts

        err = """Plug-in %s is not compatible with available host(s).

Required host(s): %s
Registered host(s): %s

Make sure the integration for your host is correctly setup
or register a new host using `pyblish.api.register_host("%s")`
""" % (plugin, repr(required_hosts), repr(hosts), required_hosts[0])

        raise TypeError(err)

    _registered_plugins[plugin.__name__] = plugin


def deregister_plugin(plugin):
    """De-register an existing plug-in

    Arguments:
        plugin (Plugin): Existing plug-in to de-register

    """

    _registered_plugins.pop(plugin.__name__)


def deregister_all_plugins():
    """De-register all plug-ins"""
    _registered_plugins.clear()


@lib.deprecated
def register_service(name, obj):
    """Register a new service

    Arguments:
        name (str): Name of service
        obj (any): Any object

    """

    _registered_services[name] = obj


@lib.deprecated
def deregister_service(name):
    """De-register an existing service by name

    Arguments:
        name (str): Name of service

    """

    _registered_services.pop(name)


@lib.deprecated
def deregister_all_services():
    """De-register all existing services"""
    _registered_services.clear()


@lib.deprecated
def registered_services():
    """Return the currently registered services as a dictionary

    .. note:: This returns a copy of the registered paths
        and can therefore not be modified directly.

    """

    return _registered_services.copy()


def register_plugin_path(path):
    """Plug-ins are looked up at run-time from directories registered here

    To register a new directory, run this command along with the absolute
    path to where you"re plug-ins are located.

    Example:
        >>> import os
        >>> my_plugins = os.path.join("server", "plugins")
        >>> register_plugin_path(my_plugins) == os.path.normpath(my_plugins)
        True

    Returns:
        Actual path added, including any post-processing

    """

    normpath = os.path.normpath(path)
    if normpath in _registered_paths:
        return log.warning("Path already registered: {0}".format(path))

    _registered_paths.append(normpath)

    return path


def deregister_plugin_path(path):
    """Remove a pyblish._registered_paths path

    Raises:
        ValueError if `path` isn't registered

    """

    normpath = os.path.normpath(path)
    try:
        _registered_paths.remove(normpath)
    except ValueError:
        return log.error("Path isn't registered: {0}".format(path))


def deregister_all_paths():
    """Mainly used in tests"""
    _registered_paths[:] = []


def registered_paths():
    """Return paths added via registration

    ..note:: This returns a copy of the registered paths
        and can therefore not be modified directly.

    """

    return list(_registered_paths)


def registered_plugins():
    """Return plug-ins added via :func:`register_plugin`

    .. note:: This returns a copy of the registered plug-ins
        and can therefore not be modified directly

    """

    plugins = list()

    for plugin in _registered_plugins.values():
        # Maintain immutability across retrievals
        copy = type(plugin.__name__, (plugin,), {})
        copy._id = plugin._id
        copy.__doc__ = plugin.__doc__
        plugins.append(copy)

    return plugins


def register_host(host):
    """Register a new host

    Registered hosts are used to filter discovered
    plug-ins by host.

    Example:
        >>> register_host("My Host")
        >>> "My Host" in registered_hosts()
        True

    """

    if host not in _registered_hosts:
        _registered_hosts.append(host)


def deregister_host(host, quiet=False):
    """Remove an already registered host

    Arguments:
        host (str): Name of host
        quiet (bool): Whether to raise an exception
            when attempting to remove a host that is
            not already registered.

    """

    try:
        _registered_hosts.remove(host)
    except Exception as e:
        if not quiet:
            raise e


def deregister_all_hosts():
    _registered_hosts[:] = []


def registered_hosts():
    """Return the currently registered hosts"""
    return list(_registered_hosts)


def current_target():
    return _registered_targets[-1] if _registered_targets else ""


def register_target(target):
    """Register a new target

    Registered targets can be used in plug-ins to determin outputs

    Example:
        >>> register_target("Studio")
        >>> "Studio" in registered_targets()
        True
        >>> current_target()
        'Studio'

    """

    if target in _registered_targets:
        idx = _registered_targets.index(target)
        _registered_targets.pop(idx)

    _registered_targets.append(target)


def deregister_target(target, quiet=False):
    """Remove an already registered target

    Arguments:
        target (str): Name of target
        quiet (bool): Whether to raise an exception
            when attempting to remove a target that is
            not already registered.

    """

    try:
        _registered_targets.remove(target)
    except Exception as e:
        if not quiet:
            raise e


def deregister_all_targets():
    _registered_targets[:] = []


def registered_targets():
    """Return the currently registered targets"""
    return list(_registered_targets)


def register_discovery_filter(callback):
    """Register a new plugin filter

    Arguments:
        callback (func): Function to execute on filter during discovery,
            takes the original of plugins to be edited in-place

    Raises:
        ValueError if `callback` is not callable.

    """

    if not callable(callback):
        raise ValueError("%s is not callable" % callback)

    _registered_plugin_filters.append(callback)


def deregister_discovery_filter(callback):
    """Deregister a plugin filter

    Arguments:
        callback (func): filtering function.

    Raises:
        ValueError on missing callback
    """

    _registered_plugin_filters.remove(callback)


def deregister_all_discovery_filters():
    """Deregisters all plugin filters"""
    _registered_plugin_filters[:] = []


def registered_discovery_filters():
    """Returns registered plugin filter callbacks"""

    return _registered_plugin_filters


def environment_paths():
    """Return paths added via environment variable"""

    plugin_path = os.environ.get("PYBLISHPLUGINPATH")
    if not plugin_path:
        return list()

    paths = plugin_path.split(os.pathsep)
    log.debug("Paths from environment: %s" % paths)

    return paths


def plugin_paths():
    """Collect paths from all sources.

    This function looks at the three potential sources of paths
    and returns a list with all of them together.

    The sources are:

    - Registered paths using :func:`register_plugin_path`,
    - Paths from the environment variable `PYBLISHPLUGINPATH`

    Returns:
        list of paths in which plugins may be locat

    """

    paths = list()

    for path in registered_paths() + environment_paths():
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
        warnings.warn("discover(): regex argument "
                      "has been deprecated and does nothing")

    plugins = dict()
    plugin_names = []

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
                with open(abspath) as f:
                    six.exec_(f.read(), module.__dict__)

                # Store reference to original module, to avoid
                # garbage collection from collecting it's global
                # imports, such as `import os`.
                sys.modules[abspath] = module

            except Exception as err:
                log.debug("Skipped: \"%s\" (%s)", mod_name, err)
                continue

            for plugin in plugins_from_module(module):
                if not ALLOW_DUPLICATES and plugin.__name__ in plugin_names:
                    log.debug("Duplicate plug-in found: %s", plugin)
                    continue

                plugin_names.append(plugin.__name__)

                plugin.__module__ = module.__file__
                key = "{0}.{1}".format(plugin.__module__, plugin.__name__)
                plugins[key] = plugin

    # Include plug-ins from registration.
    # Directly registered plug-ins take precedence.
    for plugin in registered_plugins():
        if not ALLOW_DUPLICATES and plugin.__name__ in plugin_names:
            log.debug("Duplicate plug-in found: %s", plugin)
            continue

        plugin_names.append(plugin.__name__)

        plugins[plugin.__name__] = plugin

    plugins = list(plugins.values())
    sort(plugins)  # In-place

    # In-place user-defined filter
    for filter_ in _registered_plugin_filters:
        filter_(plugins)

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
                          obj, __version__))
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

    if not isinstance(plugin.requires, six.string_types):
        log.debug("Plug-in requires must be of type string: %s", plugin)
        return False

    if not isinstance(plugin.families, list):
        log.debug(".families must be list of stirngs")
        return False

    if not isinstance(plugin.targets, list):
        log.debug(".targets must be list of strings")
        return False

    if not isinstance(plugin.hosts, list):
        log.debug(".hosts must be list of strings")
        return False

    for family in plugin.families:
        if not isinstance(family, six.string_types):
            log.debug("Families must be string")
            return False

    for host in plugin.hosts:
        if not isinstance(host, six.string_types):
            log.debug("Hosts must be string")
            return False

    if hasattr(plugin, "__invalidSignature__"):
        log.debug("Invalid signature")
        return False

    if plugin.match not in (Intersection, Subset, Exact):
        log.debug("'%s' not a supported family "
                  "matching algorithm." % plugin.match)
        log.debug("Options are "
                  "pyblish.api.Intersection, "
                  "pyblish.api.Subset and"
                  "pyblish.api.Exact")
        return False

    return True


def version_is_compatible(plugin):
    """Lookup compatibility between plug-in and current version of Pyblish

    Arguments:
        plugin (Plugin): Plug-in to test against

    """

    if not iscompatible.iscompatible(requirements=plugin.requires,
                                     version=version_info):
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

    if not isinstance(plugins, list):
        raise TypeError("plugins must be of type list")

    plugins.sort(key=lambda p: p.order)
    return plugins
