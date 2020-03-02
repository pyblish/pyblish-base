import os
import sys
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
        if record.name.startswith("pyblish"):
            self.records.append(record)


def extract_traceback(exception, fname=None):
    """Inject current traceback and store in exception.traceback.

    Also storing the formatted traceback on exception.formtatted_traceback.

    Arguments:
        exception (Exception): Exception object
        fname (str): Optionally provide a file name for the exception.
            This is necessary to inject the correct file path in the traceback.
            If plugins are registered through `api.plugin.discover`, they only
            show "<string>" instead of the actual source file.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    formatted_traceback = ''.join(traceback.format_exception(
        exc_type, exc_value, exc_traceback))
    if 'File "<string>", line' in formatted_traceback and fname is not None:
        _, lineno, func, msg = exception.traceback
        fname = os.path.abspath(fname)
        exception.traceback = (fname, lineno, func, msg)
        formatted_traceback = formatted_traceback.replace(
            'File "<string>", line',
            'File "{0}", line'.format(fname))
    exception.formatted_traceback = formatted_traceback

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
        >>> from . import plugin
        >>> plugin.register_callback(
        ...   "mysignal", lambda data: sys.stdout.write(str(data)))
        ...
        >>> emit("mysignal", data={"something": "cool"})
        {'something': 'cool'}

    """

    for callback in _registered_callbacks.get(signal, []):
        try:
            callback(**kwargs)
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


def deprecated(func):
    """Deprecation decorator

    Attach this to deprecated functions or methods.

    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
