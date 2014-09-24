
# Standard library
import os

# Local library
import pyblish.backend.lib
import pyblish

# from pyblish.vendor.nose.tools import raises

# Setup
HOST = 'python'
FAMILY = 'test.family'

package_path = pyblish.backend.lib.main_package_path()
plugin_path = os.path.join(package_path, 'backend', 'tests', 'plugins')

pyblish.deregister_all()
pyblish.register_plugin_path(plugin_path)


def test_data():
    """The data() interface works"""

    ctx = pyblish.Context()

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


def test_add_remove_instances():
    """Adding instances to context works"""
    ctx = pyblish.Context()
    inst = pyblish.Instance(name='Test', parent=ctx)
    ctx.add(inst)
    ctx.remove(inst)


def test_instance_equality():
    """Instance equality works"""
    inst1 = pyblish.Instance('Test1')
    inst2 = pyblish.Instance('Test2')
    inst3 = pyblish.Instance('Test2')

    assert inst1 != inst2
    assert inst2 == inst3


if __name__ == '__main__':
    test_add_remove_instances()
