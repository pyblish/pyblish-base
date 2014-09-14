import os
import pyblish.backend.plugin
import pyblish.backend.config

# Setup
HOST = 'python'
FAMILY = 'test.family'

registered = pyblish.backend.plugin.registered_paths
package_path = pyblish.backend.lib.main_package_path()
plugin_path = os.path.join(package_path, 'backend', 'tests', 'plugins')
pyblish.backend.plugin.deregister_all()
pyblish.backend.config.paths[:] = []


def setup():
    """Disable default plugins and only use test plugins"""
    pyblish.backend.plugin.register_plugin_path(plugin_path)


def setup_failing():
    """Expose failing plugins to discovery mechanism"""
    setup()

    # Append failing plugins
    failing_path = os.path.join(plugin_path, 'failing')
    pyblish.backend.plugin.register_plugin_path(failing_path)


def setup_duplicate():
    """Expose duplicate plugins to discovery mechanism"""
    pyblish.backend.plugin.deregister_all()
    pyblish.backend.config.paths[:] = []

    for copy in ('copy1', 'copy2'):
        path = os.path.join(plugin_path, 'duplicate', copy)
        pyblish.backend.plugin.register_plugin_path(path)


def setup_invalid():
    """Expose invalid plugins to discovery mechanism"""
    failing_path = os.path.join(plugin_path, 'invalid')
    pyblish.backend.plugin.register_plugin_path(failing_path)


def setup_full():
    """Expose a full processing chain for testing"""
    path = os.path.join(plugin_path, 'full')
    pyblish.backend.plugin.register_plugin_path(path)


def teardown():
    """Restore previously registered paths"""
    pyblish.backend.plugin.deregister_all()
    for path in registered:
        pyblish.backend.plugin.register_plugin_path(path)
