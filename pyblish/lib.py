import os
import re
import sys
import logging

_filename_ascii_strip_re = re.compile(r'[^-\w.]')
_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4',
                         'LPT1', 'LPT2', 'LPT3', 'PRN', 'NUL')


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

    Modifier from werkzeug.utils.secure_filename()

    Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.secure_fil

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
