
# Standard library
import os

# Local library
import pyblish.lib
import pyblish.plugin

from pyblish.tests.lib import (
    setup, teardown, setup_failing, HOST, FAMILY,
    setup_duplicate, setup_invalid, setup_wildcard,
    setup_empty, setup_full, setup)
from pyblish.vendor.nose.tools import *


package_path = pyblish.lib.main_package_path()
plugin_path = os.path.join(package_path, 'tests', 'plugins')

pyblish.plugin.deregister_all_paths()
pyblish.plugin.register_plugin_path(plugin_path)


def test_data():
    """The data() interface works"""

    ctx = pyblish.plugin.Context()

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
    ctx = pyblish.plugin.Context()
    inst = pyblish.plugin.Instance(name='Test', parent=ctx)
    ctx.add(inst)
    ctx.remove(inst)


def test_instance_equality():
    """Instance equality works"""
    inst1 = pyblish.plugin.Instance('Test1')
    inst2 = pyblish.plugin.Instance('Test2')
    inst3 = pyblish.plugin.Instance('Test2')

    assert inst1 != inst2
    assert inst2 == inst3


if __name__ == '__main__':
    test_add_remove_instances()
