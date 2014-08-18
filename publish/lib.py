import logging


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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
