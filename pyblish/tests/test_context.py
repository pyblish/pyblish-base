
# Standard library
import os

# Local library
import pyblish.lib
import pyblish.plugin

from pyblish.tests.lib import (
    setup_full, teardown)
from pyblish.vendor.nose.tools import with_setup

# Setup
HOST = 'python'
FAMILY = 'test.family'

package_path = pyblish.lib.main_package_path()
plugin_path = os.path.join(package_path, 'tests', 'plugins')

pyblish.plugin.deregister_all()
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


@with_setup(setup_full, teardown)
def test_limited_to_instances():
    """Only process instances specified in argument `instances`"""
    ctx = pyblish.plugin.Context()

    for name in ("Instance01", "Instance02", "Instance03"):
        inst = ctx.create_instance(name=name)
        inst.set_data("family", "full")

    plugin = pyblish.plugin.discover(regex="ValidateInstance")[0]
    assert plugin

    for inst, err in plugin().process(ctx, instances=["Instance01",
                                                      "Instance03"]):
        assert err is None

    for inst in ctx:
        name = inst.data("name")
        if name in ["Instance01", "Instance03"]:
            assert inst.data('validated', False) is True
        if name == "Instance02":
            assert inst.data('validated', False) is False

if __name__ == '__main__':
    test_add_remove_instances()
