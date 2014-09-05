import os
import pyblish.backend.plugin

# Setup
HOST = 'python'
FAMILY = 'test.family'

registered = pyblish.backend.plugin.registered_paths
package_path = pyblish.backend.lib.main_package_path()
plugin_path = os.path.join(package_path, 'backend', 'tests', 'plugins')


def setup():
    """Disable default plugins and only use test plugins"""
    pyblish.backend.plugin.deregister_all()
    pyblish.backend.plugin.register_plugin_path(plugin_path)


def setup_failing():
    """Expose failing plugins to discovery mechanism"""
    setup()

    # Append failing plugins
    failing_path = os.path.join(plugin_path, 'failing')
    pyblish.backend.plugin.register_plugin_path(failing_path)


def setup_duplicate():
    """Expose duplicate paths to discovery mechanism"""
    pyblish.backend.plugin.deregister_all()

    for copy in ('copy1', 'copy2'):
        path = os.path.join(plugin_path, 'duplicate', copy)
        pyblish.backend.plugin.register_plugin_path(path)


def teardown():
    """Restore previously registered paths"""
    pyblish.backend.plugin.deregister_all()
    for path in registered:
        pyblish.backend.plugin.register_plugin_path(path)
