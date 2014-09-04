
# Standard library
import os

# Local library
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin

# from pyblish.vendor.nose.tools import raises

# Setup
HOST = 'python'
FAMILY = 'test.family'

package_path = pyblish.backend.lib.main_package_path()
plugin_path = os.path.join(package_path, 'backend', 'tests', 'plugins')

pyblish.backend.plugin.deregister_all()
pyblish.backend.plugin.register_plugin_path(plugin_path)


def test_data():
    """The data() interface works"""

    ctx = pyblish.backend.plugin.Context()

    # Not passing a key returns all data as a dict,
    # but there is none yet.
    assert ctx.data(key=None) == dict()

    key = 'test_key'

    ctx.set_data(key=key, value=True)
    assert ctx.data(key=key) is True
    assert ctx.has_data(key=key) is True
    ctx.remove_data(key=key)
    assert ctx.data(key=key) is None
    assert ctx.has_data(key=key) is False


if __name__ == '__main__':
    import logging
    import pyblish
    log = pyblish.setup_log()
    log.setLevel(logging.DEBUG)

    test_data()
