import os
import shutil
import tempfile
import contextlib

import pyblish.plugin
from pyblish.vendor.nose.tools import (
    with_setup,
    assert_true,
    assert_equals,
    raises,
)

import lib


@contextlib.contextmanager
def tempdir():
    try:
        tempdir = tempfile.mkdtemp()
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def test_unique_id():
    """Plug-ins and instances have a unique id"""

    class MyPlugin(pyblish.plugin.Selector):
        pass

    assert_true(hasattr(MyPlugin, "id"))

    instance = pyblish.plugin.Instance("MyInstance")
    assert_true(hasattr(instance, "id"))


def test_context_from_instance():
    """Instances provide access to their parent context"""

    context = pyblish.plugin.Context()
    instance = context.create_instance("MyInstance")
    assert_equals(context, instance.context)


def test_legacy():
    """Legacy is determined by existing process_* methods"""
    class LegacyPlugin(pyblish.plugin.Selector):
        def process_context(self, context):
            pass

    class NotLegacyPlugin(pyblish.plugin.Selector):
        def process(self, context):
            pass

    assert_true(hasattr(LegacyPlugin, "__pre11__"))
    assert_equals(LegacyPlugin.__pre11__, True)
    assert_true(hasattr(NotLegacyPlugin, "__pre11__"))
    assert_equals(NotLegacyPlugin.__pre11__, False)


def test_asset():
    """Using asset over instance works fine"""
    context = pyblish.plugin.Context()

    asseta = context.create_asset("MyAssetA", family="myFamily")
    assetb = context.create_asset("MyAssetB", family="myFamily")

    assert_true(asseta in context)
    assert_true(assetb in context)


@with_setup(lib.setup_empty, lib.teardown)
def test_import_mechanism_duplication():
    """Plug-ins don't linger after a second discovery

    E.g. when changing the name of a plug-in and then rediscover
    the previous plug-ins is still around.

    """

    with tempdir() as temp:
        print("Writing temporarily to: %s" % temp)
        module = os.path.join(temp, "selector.py")
        pyblish.api.register_plugin_path(temp)

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MySelector(pyblish.api.Selector):
    pass
""")

        with open(module) as f:
            print("File contents after first write:")
            print(f.read())

        # MySelector should be accessible by now
        plugins = [p.__name__ for p in pyblish.api.discover()]

        assert "MySelector" in plugins, plugins
        assert "MyOtherSelector" not in plugins, plugins

        # Remove module, and it's .pyc equivalent
        [os.remove(os.path.join(temp, fname))
         for fname in os.listdir(temp)]

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MyOtherSelector(pyblish.api.Selector):
    pass
""")

        with open(module) as f:
            print("File contents after second write:")
            print(f.read())

        # MySelector should be gone in favour of MyOtherSelector
        plugins = [p.__name__ for p in pyblish.api.discover()]

        assert "MyOtherSelector" in plugins, plugins
        assert "MySelector" not in plugins, plugins


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_unsupported_hosts():
    """Cannot register a unsupported plug-in in an unsupported host"""

    class Unsupported(pyblish.api.Plugin):
        hosts = ["unsupported"]

    pyblish.api.register_plugin(Unsupported)


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_unsupported_version():
    """Cannot register a plug-in of an unsupported version"""

    class Unsupported(pyblish.api.Plugin):
        requires = (999, 999, 999)

    pyblish.api.register_plugin(Unsupported)


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_malformed():
    """Cannot register a malformed plug-in"""

    class Unsupported(pyblish.api.Plugin):
        families = True
        hosts = None

    pyblish.api.register_plugin(Unsupported)


@with_setup(lib.setup_empty, lib.teardown)
def test_temporarily_disabled_plugins():
    """Plug-ins as files starting with an underscore are hidden"""

    discoverable = """
import pyblish.api

class Discoverable(pyblish.api.Plugin):
    pass
"""

    notdiscoverable = """
import pyblish.api

class NotDiscoverable(pyblish.api.Plugin):
    pass
"""

    with tempdir() as d:
        pyblish.api.register_plugin_path(d)

        with open(os.path.join(d, "discoverable.py"), "w") as f:
            f.write(discoverable)

        with open(os.path.join(d, "_undiscoverable.py"), "w") as f:
            f.write(notdiscoverable)

        plugins = [p.__name__ for p in pyblish.api.discover()]
        assert "Discoverable" in plugins
        assert "NotDiscoverable" not in plugins


@with_setup(lib.setup_empty, lib.teardown)
def test_repair_context_backwardscompat():
    """Plug-ins with repair-context are reprogrammed appropriately"""

    class ValidateInstances(pyblish.api.Validator):
        def repair_context(self, context):
            pass

    assert hasattr(ValidateInstances, "repair")
    assert not hasattr(ValidateInstances, "repair_context")


@with_setup(lib.setup_empty, lib.teardown)
def test_unique_logger():
    """A unique logger is applied to every plug-in"""

    count = {"#": 0}

    class MyPlugin(pyblish.api.Plugin):
        def process(self, context):
            self.log.debug("Hello world")
            count["#"] += 1

    pyblish.api.register_plugin(MyPlugin)

    context = pyblish.util.publish()

    assert_equals(count["#"], 1)
    print context.data("results")

    results = context.data("results")[0]
    records = results["records"]
    hello_world = records[0]
    assert_equals(hello_world.msg, "Hello world")


@with_setup(lib.setup_empty, lib.teardown)
def test_current_host():
    """pyblish.api.current_host works"""
    pyblish.plugin.register_host("myhost")
    assert_equals(pyblish.plugin.current_host(), "myhost")


@with_setup(lib.setup_empty, lib.teardown)
def test_register_host():
    """Registering and deregistering hosts works fine"""
    pyblish.plugin.register_host("myhost")
    assert "myhost" in pyblish.plugin.registered_hosts()
    pyblish.plugin.deregister_host("myhost")
    assert "myhost" not in pyblish.plugin.registered_hosts()


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

    exec code in module.__dict__

    plugins = pyblish.plugin.plugins_from_module(module)

    assert [p.id for p in plugins] == ["MyPlugin"], plugins


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

    exec code in module.__dict__
    MyPlugin = pyblish.plugin.plugins_from_module(module)[0]
    assert MyPlugin.id == "MyPlugin"

    assert_true(MyPlugin().process(True))
    assert_true(MyPlugin().module_is_present())
    assert_true(MyPlugin().local_variable_is_present())

    try:
        tempdir = tempfile.mkdtemp()
        tempplugin = os.path.join(tempdir, "my_plugin.py")
        with open(tempplugin, "w") as f:
            f.write(code)

        pyblish.api.register_plugin_path(tempdir)
        plugins = pyblish.api.discover()

    finally:
        shutil.rmtree(tempdir)

    assert len(plugins) == 1

    MyPlugin = plugins[0]

    assert_true(MyPlugin().process(True))
    assert_true(MyPlugin().module_is_present())
    assert_true(MyPlugin().local_variable_is_present())


@with_setup(lib.setup_empty, lib.teardown)
def test_data_dict():
    """.data is a pure dictionary"""

    context = pyblish.api.Context()
    instance = context.create_instance("MyInstance")
    assert isinstance(context.data, dict)
    assert isinstance(instance.data, dict)

    context.data["key"] = "value"
    assert context.data["key"] == "value"

    instance.data["key"] = "value"
    assert instance.data["key"] == "value"

    # Backwards compatibility
    assert context.data("key") == "value"
    assert instance.data("key") == "value"
    assert instance.data("name") == "MyInstance"
    # This returns (a copy of) the full dictionary
    assert context.data() == context.data


@with_setup(lib.setup_empty, lib.teardown)
def test_action():
    """Running an action is like running a plugin"""
    count = {"#": 0}

    class MyAction(pyblish.plugin.Action):
        def process(self, context):
            count["#"] += 1

    class MyPlugin(pyblish.plugin.Plugin):
        actions = [MyAction]

        def process(self, context):
            pass

    context = pyblish.api.Context()
    pyblish.plugin.process(
        plugin=MyPlugin,
        context=context,
        action="MyAction")

    assert count["#"] == 1


@with_setup(lib.setup_empty, lib.teardown)
def test_actions():
    class MyAction(pyblish.plugin.Action):
        def process(self, context):
            context.data["key"] = "value"

    context = pyblish.api.Context()
    pyblish.plugin.process(MyAction, context)
    assert "key" in context.data


@with_setup(lib.setup_empty, lib.teardown)
def test_action_error_checking():
    class MyActionValid(pyblish.plugin.Action):
        on = "all"

    class MyActionInvalid(pyblish.plugin.Action):
        on = "invalid"

    assert MyActionValid.__error__ is None
    assert MyActionInvalid.__error__


@with_setup(lib.setup_empty, lib.teardown)
def test_action_printing():
    class MyAction(pyblish.plugin.Action):
        pass

    print(MyAction())
    print repr(MyAction())

    assert str(MyAction()) == "MyAction"
    assert repr(MyAction()) == "pyblish.plugin.MyAction('MyAction')"


@with_setup(lib.setup_empty, lib.teardown)
def test_category_separator():
    assert issubclass(pyblish.plugin.Category("Test"),
                      pyblish.plugin.Action)
    assert issubclass(pyblish.plugin.Separator,
                      pyblish.plugin.Action)


def test_superclass_process_is_empty():
    """Superclass process() is empty"""
    def e():
        """Doc"""

    assert pyblish.api.Plugin.process.__code__.co_code == e.__code__.co_code
    assert pyblish.api.Plugin.repair.__code__.co_code == e.__code__.co_code


def test_plugin_source_path():
    """Plugins discovered carry a source path"""

    import sys
    plugin = pyblish.plugin.discover()[0]
    module = sys.modules[plugin.__module__]
    assert hasattr(module, "__file__")

    # Also works with inspect.getfile
    import inspect
    assert inspect.getfile(plugin) == module.__file__


@with_setup(lib.setup_empty, lib.teardown)
def test_multi_families():
    """Instances with multiple families works well"""

    count = {"#": 0}

    class CollectInstance(pyblish.api.Collector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["families"] = ["geometry", "human"]

    class ValidateHumans(pyblish.api.Validator):
        families = ["human"]

        def process(self, instance):
            assert "human" in instance.data["families"]
            count["#"] += 10

    class ValidateGeometry(pyblish.api.Validator):
        families = ["geometry"]

        def process(self, instance):
            assert "geometry" in instance.data["families"]
            count["#"] += 100

    for plugin in (CollectInstance, ValidateHumans, ValidateGeometry):
        pyblish.api.register_plugin(plugin)

    pyblish.util.publish()

    assert count["#"] == 110, count["#"]
