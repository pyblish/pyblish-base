import os
import sys
import shutil
import tempfile
import contextlib

# import pyblish
from pyblish import api, _lib, _plugin
from pyblish._vendor import six

# Setup
HOST = 'python'
FAMILY = 'test.family'

REGISTERED = _plugin.registered_paths()
PACKAGEPATH = _lib.main_package_path()
ENVIRONMENT = os.environ.get("PYBLISHPLUGINPATH", "")
PLUGINPATH = os.path.join(PACKAGEPATH, '..', 'tests', 'plugins')


def setup():
    """Disable default plugins and only use test plugins"""
    _plugin.deregister_all_paths()


def setup_empty():
    """Disable all plug-ins"""
    setup()
    _plugin.deregister_all_plugins()
    _plugin.deregister_all_paths()
    _plugin.deregister_all_hosts()
    _plugin.deregister_all_callbacks()


def teardown():
    """Restore previously REGISTERED paths"""

    _plugin.deregister_all_paths()
    for path in REGISTERED:
        _plugin.register_plugin_path(path)

    os.environ["PYBLISHPLUGINPATH"] = ENVIRONMENT
    api.deregister_all_plugins()
    api.deregister_all_hosts()
    api.deregister_test()
    api.__init__()


@contextlib.contextmanager
def captured_stdout():
    """Temporarily reassign stdout to a local variable"""
    try:
        sys.stdout = six.StringIO()
        yield sys.stdout
    finally:
        sys.stdout = sys.__stdout__


@contextlib.contextmanager
def captured_stderr():
    """Temporarily reassign stderr to a local variable"""
    try:
        sys.stderr = six.StringIO()
        yield sys.stderr
    finally:
        sys.stderr = sys.__stderr__


@contextlib.contextmanager
def tempdir():
    """Provide path to temporary directory"""
    try:
        tempdir = tempfile.mkdtemp()
        yield tempdir
    finally:
        shutil.rmtree(tempdir)
