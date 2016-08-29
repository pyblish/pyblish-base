import os
import shutil
import tempfile

from pyblish import api, util, _plugin
from pyblish._vendor import six
from nose.tools import (
    with_setup,
    assert_true,
)

from .. import lib


def test_plugins_from_module():
    """Getting plug-ins from a module works well"""
    import types

    module = types.ModuleType("myplugin")
    code = """
import pyblish.api

class MyPlugin(pyblish.api.Plugin):
    def process(self, context):
        pass

class NotSubclassed(object):
    def process(self, context):
        pass

def not_a_plugin():
    pass


class InvalidPlugin(pyblish.api.Plugin):
    families = False


class NotCompatible(pyblish.api.Plugin):
    hosts = ["not_compatible"]


class BadRequires(pyblish.api.Plugin):
    requires = None


class BadHosts(pyblish.api.Plugin):
    hosts = None


class BadFamilies(pyblish.api.Plugin):
    families = None


class BadHosts2(pyblish.api.Plugin):
    hosts = [None]


class BadFamilies2(pyblish.api.Plugin):
    families = [None]


"""

    six.exec_(code, module.__dict__)

    plugins = _plugin.plugins_from_module(module)

    assert [p.__name__ for p in plugins] == ["MyPlugin"], plugins


@with_setup(lib.setup_empty, lib.teardown)
def test_discover_globals():
    """Modules imported in a plug-in are preserved in it's methods"""

    import types

    module = types.ModuleType("myplugin")
    code = """
import pyblish.api
import threading

local_variable_is_present = 5


class MyPlugin(pyblish.api.Plugin):
    def module_is_present(self):
        return True if threading else False

    def local_variable_is_present(self):
        return True if local_variable_is_present else False

    def process(self, context):
        return True if context else False

"""

    six.exec_(code, module.__dict__)
    MyPlugin = _plugin.plugins_from_module(module)[0]
    assert MyPlugin.__name__ == "MyPlugin"

    assert_true(MyPlugin().process(True))
    assert_true(MyPlugin().module_is_present())
    assert_true(MyPlugin().local_variable_is_present())

    try:
        tempdir = tempfile.mkdtemp()
        tempplugin = os.path.join(tempdir, "my_plugin.py")
        with open(tempplugin, "w") as f:
            f.write(code)

        api.register_plugin_path(tempdir)
        plugins = api.discover()

    finally:
        shutil.rmtree(tempdir)

    assert len(plugins) == 1

    MyPlugin = plugins[0]

    assert_true(MyPlugin().process(True))
    assert_true(MyPlugin().module_is_present())
    assert_true(MyPlugin().local_variable_is_present())


@with_setup(lib.setup_empty, lib.teardown)
def test_multi_families():
    """Instances with multiple families works well"""

    count = {"#": 0}

    class CollectInstance(api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["families"] = ["geometry", "human"]

    class ValidateHumans(api.Validator):
        families = ["human"]

        def process(self, instance):
            assert "human" in instance.data["families"]
            count["#"] += 10

    class ValidateGeometry(api.Validator):
        families = ["geometry"]

        def process(self, instance):
            assert "geometry" in instance.data["families"]
            count["#"] += 100

    for plugin in (CollectInstance, ValidateHumans, ValidateGeometry):
        api.register_plugin(plugin)

    util.publish()

    assert count["#"] == 110, count["#"]
