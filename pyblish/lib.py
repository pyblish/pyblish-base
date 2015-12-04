import os
import re
import sys
import logging
import datetime
import traceback

_filename_ascii_strip_re = re.compile(r'[^-\w.]')
_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4',
                         'LPT1', 'LPT2', 'LPT3', 'PRN', 'NUL')


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
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
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
        ...   print True
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


def format_filename(filename):
    """Convert arbitrary string to valid filename, django-style.

    Modified from django.utils.text.get_valid_filename()

    Returns the given string converted to a string that can be used for a clean
    filename. Specifically, leading and trailing spaces are removed; other
    spaces are converted to underscores; and anything that is not a unicode
    alphanumeric, dash, underscore, or dot, is removed.

    Usage:
        >>> format_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'
        >>> format_filename("something^_SD.dda.//fd/ad.exe")
        'something_SD.dda.fdad.exe'
        >>> format_filename("Napoleon_:namespaces_GRP|group1_GRP")
        'Napoleon_namespaces_GRPgroup1_GRP'

    """

    filename = filename.strip().replace(' ', '_')

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if os.name == 'nt' and filename and \
       filename.split('.')[0].upper() in _windows_device_files:
        filename = '_' + filename

    return re.sub(r'(?u)[^-\w.]', '', filename)


def format_filename2(filename):
    """Convert arbitrary string to valid filename, werkzeug-style.

    Modified from werkzeug.utils.secure_filename()

    Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`. The filename returned is an ASCII only string
    for maximum portability.

    On windows system the function also makes sure that the file is not
    named after one of the special device files.

    Arguments:
        filename (str): the filename to secure

    Usage:
        >>> format_filename2("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'
        >>> format_filename2("something^_SD.dda.//fd/ad.exe")
        'something_SD.dda._fd_ad.exe'
        >>> format_filename2("Napoleon_:namespaces_GRP|group1_GRP")
        'Napoleon_namespaces_GRPgroup1_GRP'

    .. warning:: The function might return an empty filename.  It's your
        responsibility to ensure that the filename is unique and that you
        generate random filename if the function returned an empty one.

    .. versionadded:: 1.0.9

    """

    if isinstance(filename, unicode):
        from unicodedata import normalize
        filename = normalize('NFKD', filename).encode('ascii', 'ignore')

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                   filename.split()))).strip('._')

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if os.name == 'nt' and filename and \
       filename.split('.')[0].upper() in _windows_device_files:
        filename = '_' + filename

    return filename


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


def import_module(name, package=None):
    """Import a module

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """

    def _resolve_name(name, package, level):
        """Return the absolute name of the module to be imported."""
        if not hasattr(package, 'rindex'):
            raise ValueError("'package' not set to a string")
        dot = len(package)
        for x in xrange(level, 1, -1):
            try:
                dot = package.rindex('.', 0, dot)
            except ValueError:
                raise ValueError("attempted relative import beyond top-level "
                                 "package")
        return "%s.%s" % (package[:dot], name)

    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)

    return sys.modules[name]
