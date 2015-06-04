import os

import pyblish
import pyblish.cli
import pyblish.plugin

config = pyblish.plugin.Config()

# Setup
HOST = 'python'
FAMILY = 'test.family'

REGISTERED = pyblish.plugin.registered_paths()
PACKAGEPATH = pyblish.lib.main_package_path()
ENVIRONMENT = os.environ.get("PYBLISHPLUGINPATH", "")
PLUGINPATH = os.path.join(PACKAGEPATH, '..', 'tests', 'plugins')


def setup():
    """Disable default plugins and only use test plugins"""
    config = pyblish.plugin.Config()
    config['paths'] = []

    pyblish.plugin.deregister_all_paths()


def setup_empty():
    """Disable all plug-ins"""
    setup()
    pyblish.plugin.deregister_all_paths()


def teardown():
    """Restore previously REGISTERED paths"""

    # Clear singletons
    pyblish.plugin.Config._instance = None

    pyblish.plugin.deregister_all_paths()
    for path in REGISTERED:
        pyblish.plugin.register_plugin_path(path)

    os.environ["PYBLISHPLUGINPATH"] = ENVIRONMENT
    pyblish.api.deregister_all_plugins()
