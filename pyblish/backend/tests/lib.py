import os

import pyblish
import pyblish.backend.plugin


# Setup
HOST = 'python'
FAMILY = 'test.family'

REGISTERED = pyblish.backend.plugin.registered_paths()
PACKAGEPATH = pyblish.backend.lib.main_package_path()
PLUGINPATH = os.path.join(PACKAGEPATH, 'backend', 'tests', 'plugins')


def setup():
    """Disable default plugins and only use test plugins"""
    config = pyblish.Config()
    config['paths'] = []

    pyblish.backend.plugin.deregister_all()
    pyblish.backend.plugin.register_plugin_path(PLUGINPATH)


def setup_failing():
    """Expose failing plugins to discovery mechanism"""
    setup()

    # Append failing plugins
    failing_path = os.path.join(PLUGINPATH, 'failing')
    pyblish.backend.plugin.register_plugin_path(failing_path)


def setup_duplicate():
    """Expose duplicate plugins to discovery mechanism"""
    pyblish.backend.plugin.deregister_all()

    config = pyblish.Config()
    config['paths'] = []

    for copy in ('copy1', 'copy2'):
        path = os.path.join(PLUGINPATH, 'duplicate', copy)
        pyblish.backend.plugin.register_plugin_path(path)


def setup_wildcard():
    pyblish.backend.plugin.deregister_all()

    config = pyblish.Config()
    config['paths'] = []

    wildcard_path = os.path.join(PLUGINPATH, 'wildcards')
    pyblish.backend.plugin.register_plugin_path(wildcard_path)


def setup_invalid():
    """Expose invalid plugins to discovery mechanism"""
    pyblish.backend.plugin.deregister_all()
    failing_path = os.path.join(PLUGINPATH, 'invalid')
    pyblish.backend.plugin.register_plugin_path(failing_path)


def setup_full():
    """Expose a full processing chain for testing"""
    pyblish.backend.plugin.deregister_all()
    path = os.path.join(PLUGINPATH, 'full')
    pyblish.backend.plugin.register_plugin_path(path)


def setup_echo():
    """Plugins that output information"""
    pyblish.backend.plugin.deregister_all()

    config = pyblish.Config()
    config['paths'] = []

    path = os.path.join(PLUGINPATH, 'echo')
    pyblish.backend.plugin.register_plugin_path(path)


def teardown():
    """Restore previously REGISTERED paths"""

    # Clear singletons
    pyblish.backend.plugin.Context._instance = None
    pyblish.Config._instance = None

    pyblish.backend.plugin.deregister_all()
    for path in REGISTERED:
        pyblish.backend.plugin.register_plugin_path(path)
