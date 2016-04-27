
# Standard library
import os

# Local library
import pyblish.lib
import pyblish.plugin

from . import lib
from nose.tools import (
    with_setup,
    raises
)


package_path = pyblish.lib.main_package_path()
plugin_path = os.path.join(package_path, 'tests', 'plugins')

pyblish.plugin.deregister_all_paths()
pyblish.plugin.register_plugin_path(plugin_path)


@with_setup(lib.setup, lib.teardown)
def test_data():
    """The data() interface works"""

    ctx = pyblish.plugin.Context()

    # Not passing a key returns all data as a dict,
    # but there is none yet.
    assert ctx.data(key=None) == dict(), ctx.data(key=None)

    key = 'test_key'

    ctx.set_data(key=key, value=True)
    assert ctx.data(key=key) is True
    assert ctx.has_data(key=key) is True
    ctx.remove_data(key=key)
    assert ctx.data(key=key) is None
    assert ctx.has_data(key=key) is False


@with_setup(lib.setup, lib.teardown)
def test_add_remove_instances():
    """Adding instances to context works"""
    ctx = pyblish.plugin.Context()
    inst = pyblish.plugin.Instance(name='Test', parent=ctx)
    ctx.remove(inst)


@with_setup(lib.setup, lib.teardown)
def test_instance_equality():
    """Instance equality works"""
    inst1 = pyblish.plugin.Instance('Test1')
    inst2 = pyblish.plugin.Instance('Test2')
    inst3 = pyblish.plugin.Instance('Test2')

    assert inst1 != inst2
    assert inst2 != inst3


def test_context_itemgetter():
    """Context.get() works"""
    context = pyblish.api.Context()
    instanceA = context.create_instance("MyInstanceA")
    instanceB = context.create_instance("MyInstanceB")

    assert context[instanceA.id].name == "MyInstanceA"
    assert context[instanceB.id].name == "MyInstanceB"
    assert context.get(instanceA.id).name == "MyInstanceA"
    assert context.get(instanceB.id).name == "MyInstanceB"
    assert context[0].name == "MyInstanceA"
    assert context[1].name == "MyInstanceB"


def test_in():
    """Querying whether an Instance is in a Context works"""

    context = pyblish.api.Context()
    instance = context.create_instance("MyInstance")
    assert instance.id in context
    assert "NotExist" not in context


def test_add_to_context():
    """Adding to Context is deprecated, but still works"""
    context = pyblish.api.Context()
    instance = pyblish.api.Instance("MyInstance")
    context.add(instance)
    context.remove(instance)


@raises(KeyError)
def test_context_getitem_nonexisting():
    """Getting a nonexisting item from Context throws a KeyError"""

    context = pyblish.api.Context()
    context.create_instance("MyInstance")
    assert context.get("NotExist") is None
    context["NotExist"]


@raises(IndexError)
def test_context_getitem_outofrange():
    """Getting a item out of range throws an IndexError"""

    context = pyblish.api.Context()
    context.create_instance("MyInstance")
    context[10000]


def test_context_getitem_validrange():
    """Getting an existing item works well"""

    context = pyblish.api.Context()
    context.create_instance("MyInstance")
    assert context[0].data["name"] == "MyInstance"


def test_context_instance_unique_id():
    """Same named instances have unique ids"""

    context = pyblish.api.Context()
    instance1 = context.create_instance("MyInstance")
    instance2 = context.create_instance("MyInstance")
    assert instance1.id != instance2.id


if __name__ == '__main__':
    test_add_remove_instances()
