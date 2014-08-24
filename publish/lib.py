import os
import logging
import inspect


def log(cls):
    """Attach logger to `cls`

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


def main_package_path():
    """Return path of main publish package"""
    lib_py_path = os.path.abspath(inspect.stack()[0][1])
    package_path = os.path.dirname(lib_py_path)
    return package_path


if __name__ == '__main__':
    import doctest
    doctest.testmod()
