import os
import sys
import types
import weakref
import logging
import datetime
import warnings
import traceback
import functools

from . import _registered_callbacks
from .vendor import six


def inrange(number, base, offset=0.5):
    r"""Evaluate whether `number` is within `base` +- `offset`

    Lower bound is *included* whereas upper bound is *excluded*
    so as to allow for ranges to be stacked up against each other.
    For example, an offset of 0.5 and a base of 1 evenly stacks
    up against a base of 2 with identical offset.

    Arguments:
        number (float): Number to consider
        base (float): Center of range
        offset (float, optional): Amount of offset from base

    Usage:
        >>> inrange(0, base=1, offset=0.5)
        False
        >>> inrange(0.4, base=1, offset=0.5)
        False
        >>> inrange(1.4, base=1, offset=0.5)
        True
        >>> # Lower bound is included
        >>> inrange(0.5, base=1, offset=0.5)
        True
        >>> # Upper bound is excluded
        >>> inrange(1.5, base=1, offset=0.5)
        False

    """

    return (base - offset) <= number < (base + offset)


class MessageHandler(logging.Handler):
    def __init__(self, records, *args, **kwargs):
        # Not using super(), for compatibility with Python 2.6
        logging.Handler.__init__(self, *args, **kwargs)
        self.records = records

    def emit(self, record):
        self.records.append(record)


def extract_traceback(exception):
    """Inject current traceback and store in exception"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exception.traceback = traceback.extract_tb(exc_traceback)[-1]
    del(exc_type, exc_value, exc_traceback)


def time():
    """Return ISO formatted string representation of current UTC time."""
    return '%sZ' % datetime.datetime.utcnow().isoformat()


class ItemList(list):
    """List with keys

    Raises:
        KeyError is item is not in list

    Example:
        >>> Obj = type("Object", (object,), {})
        >>> obj = Obj()
        >>> obj.name = "Test"
        >>> l = ItemList(key="name")
        >>> l.append(obj)
        >>> l[0] == obj
        True
        >>> l["Test"] == obj
        True
        >>> try:
        ...   l["NotInList"]
        ... except KeyError:
        ...   print(True)
        True
        >>> obj == l.get("Test")
        True
        >>> l.get("NotInList") == None
        True

    """

    def __init__(self, key, object=list()):
        super(ItemList, self).__init__(object)
        self.key = key

    def __getitem__(self, index):
        if isinstance(index, int):
            return super(ItemList, self).__getitem__(index)

        for item in self:
            if getattr(item, self.key) == index:
                return item

        raise KeyError("%s not in list" % index)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def log(cls):
    """Decorator for attaching a logger to the class `cls`

    Loggers inherit the syntax {module}.{submodule}

    Example
        >>> @log
        ... class MyClass(object):
        ...     pass
        >>>
        >>> myclass = MyClass()
        >>> myclass.log.info('Hello World')

    """

    module = cls.__module__
    name = cls.__name__

    # Package name appended, for filtering of LogRecord instances
    logname = "pyblish.%s.%s" % (module, name)
    cls.log = logging.getLogger(logname)

    # All messages are handled by root-logger
    cls.log.propagate = True

    return cls


def parse_environment_paths(paths):
    """Given a (semi-)colon separated string of paths, return a list

    Example:
        >>> import os
        >>> parse_environment_paths("path1" + os.pathsep + "path2")
        ['path1', 'path2']
        >>> parse_environment_paths("path1" + os.pathsep)
        ['path1', '']

    Arguments:
        paths (str): Colon or semi-colon (depending on platform)
            separated string of paths.

    Returns:
        list of paths as string.

    """

    paths_list = list()

    for path in paths.split(os.pathsep):
        paths_list.append(path)

    return paths_list


def get_formatter():
    """Return a default Pyblish formatter for logging

    Example:
        >>> import logging
        >>> log = logging.getLogger("myLogger")
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(get_formatter())

    """

    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s',
        '%H:%M:%S')
    return formatter


def setup_log(root='pyblish', level=logging.DEBUG):
    """Setup a default logger for Pyblish

    Example:
        >>> log = setup_log()
        >>> log.info("Hello, World")

    """

    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(root)
    log.propagate = True
    log.handlers[:] = []
    log.addHandler(handler)

    log.setLevel(level)

    return log


def main_package_path():
    """Return path of main pyblish package"""
    lib_py_path = sys.modules[__name__].__file__
    package_path = os.path.dirname(lib_py_path)
    return package_path


def emit(signal, **kwargs):
    """Trigger registered callbacks

    Keyword arguments are passed from caller to callee.

    Arguments:
        signal (string): Name of signal emitted

    Example:
        >>> import sys
        >>> def mycallback(data):
        ...     sys.stdout.write(str(data))
        ...
        >>> register_callback("mysignal", mycallback)
        ...
        >>> emit("mysignal", data={"something": "cool"})
        {'something': 'cool'}

    """

    for callback in _registered_callbacks.get(signal, {}).values():
        try:
            callback(**kwargs)

        except ReferenceError:
            # Ignore end-of-life references
            print("not calling %s" % signal)
            pass

        except Exception:
            file = six.StringIO()
            traceback.print_exc(file=file)
            sys.stderr.write(file.getvalue())
            # Why the roundabout through StringIO?
            #
            # tests.lib.captured_stderr attempts to capture stderr
            # but doing so with plain print_exc() results in a type
            # error in Python 3. I'm not confident in Python 3 unicode
            # handling so there is likely a better way to solve this.
            #
            # TODO(marcus): Make it prettier


def register_callback(signal, callback):
    """Register a new callback

    Arguments:
        signal (string): Name of signal to register the callback with.
        callback (func): Function to execute when a signal is emitted.

    Raises:
        ValueError if `callback` is not callable.

    """

    if not hasattr(callback, "__call__"):
        raise ValueError("%s must be callable" % callback)

    if signal not in _registered_callbacks:
        # Need to store in a dictionary so as to
        # enable removal via deregister_callback,
        # since the actual function is not comparable
        # to its weak reference equivalent.

        _registered_callbacks[signal] = weakref.WeakValueDictionary()

    name = callback.__name__
    callbacks = _registered_callbacks[signal]

    if name in callbacks:
        raise ValueError(
            "Callback by this name already registered: \"%s\"" % name
        )

    # Use weak reference such that connected callbacks
    # can safely be garbage collected without interference
    # from observers.
    callbacks[name] = callback


def deregister_callback(signal, callback):
    """Deregister a callback

    Arguments:
        signal (string): Name of signal to deregister the callback with.
        callback (func): Function to execute when a signal is emitted.

    Raises:
        KeyError on missing signal or callback

    """

    _registered_callbacks[signal].pop(callback.__name__)

    # Erase empty member
    if not _registered_callbacks[signal]:
        _registered_callbacks.pop(signal)


def deregister_all_callbacks():
    """Deregisters all callback"""

    _registered_callbacks.clear()


def registered_callbacks():
    """Returns registered callbacks"""

    return _registered_callbacks.keys()


def deprecated(func):
    """Deprecation decorator

    Attach this to deprecated functions or methods.

    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.version_info[0] == 2:
            warnings.warn_explicit(
                "Call to deprecated function %s." % func.__name__,
                category=DeprecationWarning,
                filename=func.func_code.co_filename,
                lineno=func.func_code.co_firstlineno + 1)
        return func(*args, **kwargs)
    return wrapper


class WeakRef(object):
    """Alternative weak reference with support for instancemethods

    Usage:
        >>> import weakref
        >>> class MyClass(object):
        ...   def func(self):
        ...     pass
        ...
        >>> inst = MyClass()
        >>> ref = weakref.ref(inst.func)
        >>> ref() is None
        True
        >>> ref = WeakRef(inst.func)
        >>> ref() is None
        False

    """

    def __init__(self, func):
        try:
            if func.im_self is not None:
                # Bound method
                self._instance = weakref.ref(func.im_self)
            else:
                # Unbound method
                self._instance = None

            self._func = weakref.ref(func.im_func)
            self._class = weakref.ref(func.im_class)

        except AttributeError:
            # Not a method
            self._instance = None
            self._class = None
            self._func = weakref.ref(func)

    def __call__(self):
        if self.is_dead():
            return None

        if self._instance is None:
            return self._func()

        return types.MethodType(self._func(), self._instance(), self._class())

    def is_dead(self):
        """Is the reference dead?

        Returns True if the referenced callable was a bound method and
        the instance no longer exists. Otherwise, return False.

        """

        return self._instance is not None and self._instance() is None

    def __eq__(self, other):
        try:
            return type(self) is type(other) and self() == other()
        except:
            return False

    def __ne__(self, other):
        return not self == other
