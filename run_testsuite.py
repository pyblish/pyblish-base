import os
import sys
import warnings

# Expose Pyblish to PYTHONPATH
path = os.path.dirname(__file__)
sys.path.insert(0, path)

import nose
from pyblish.vendor import mock

warnings.warn = mock.MagicMock()

# Support for Python 3.10+
if sys.version_info >= (3, 10):
    import collections
    collections.Callable = collections.abc.Callable

    import inspect

    def getargspec(*args, **kwargs):
        res = inspect.getfullargspec(*args, **kwargs)
        return res[:4]

    inspect.getargspec = getargspec


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['--exclude=vendor', '--with-doctest', '--verbose'])
    nose.main(argv=argv)
