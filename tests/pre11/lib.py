import os

from pyblish import api, _lib

# Setup
HOST = 'python'
FAMILY = 'test.family'

REGISTERED = api.registered_paths()
PACKAGEPATH = _lib.main_package_path()
PLUGINPATH = os.path.join(PACKAGEPATH, '..', 'tests', 'pre11', 'plugins')
ENVIRONMENT = os.environ.get("PYBLISHPLUGINPATH", "")


def setup():
    """Disable default plugins and only use test plugins"""
    api.deregister_all_paths()
    api.register_plugin_path(PLUGINPATH)


def setup_empty():
    """Disable all plug-ins"""
    setup()
    api.deregister_all_plugins()
    api.deregister_all_paths()


def setup_failing():
    """Expose failing plugins to discovery mechanism"""
    setup()

    # Append failing plugins
    failing_path = os.path.join(PLUGINPATH, 'failing')
    api.register_plugin_path(failing_path)


def setup_duplicate():
    """Expose duplicate plugins to discovery mechanism"""
    api.deregister_all_paths()

    for copy in ('copy1', 'copy2'):
        path = os.path.join(PLUGINPATH, 'duplicate', copy)
        api.register_plugin_path(path)


def setup_wildcard():
    api.deregister_all_paths()

    wildcard_path = os.path.join(PLUGINPATH, 'wildcards')
    api.register_plugin_path(wildcard_path)
    print(wildcard_path)


def setup_invalid():
    """Expose invalid plugins to discovery mechanism"""
    api.deregister_all_paths()
    failing_path = os.path.join(PLUGINPATH, 'invalid')
    api.register_plugin_path(failing_path)


def setup_full():
    """Expose a full processing chain for testing"""
    setup()
    api.deregister_all_paths()
    path = os.path.join(PLUGINPATH, 'full')
    api.register_plugin_path(path)


def setup_echo():
    """Plugins that output information"""
    api.deregister_all_paths()

    path = os.path.join(PLUGINPATH, 'echo')
    api.register_plugin_path(path)


def teardown():
    """Restore previously REGISTERED paths"""

    api.deregister_all_paths()
    for path in REGISTERED:
        api.register_plugin_path(path)

    os.environ["PYBLISHPLUGINPATH"] = ENVIRONMENT
    api.deregister_all_plugins()


# CLI Fixtures


def setup_cli():
    os.environ["PYBLISHPLUGINPATH"] = PLUGINPATH


def setup_failing_cli():
    """Expose failing plugins to CLI discovery mechanism"""
    # Append failing plugins
    failing_path = os.path.join(PLUGINPATH, 'failing_cli')
    os.environ["PYBLISHPLUGINPATH"] = failing_path
