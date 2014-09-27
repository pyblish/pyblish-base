import os
import sys
import re
import logging


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
    logname = "%s.%s" % (module, name)
    cls.log = logging.getLogger(logname)
    return cls


def format_filename(filename):
    """Convert arbitrary string to valid filename

    Modified copy from django.utils.text.get_valid_filename()

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
    return re.sub(r'(?u)[^-\w.]', '', filename)


def get_formatter():
    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s',
        '%H:%M:%S')
    return formatter


def setup_log(root='pyblish', level=logging.DEBUG):
    log = logging.getLogger(root)

    if log.handlers:
        return log.handlers[0]

    log.setLevel(level)

    formatter = get_formatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

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
