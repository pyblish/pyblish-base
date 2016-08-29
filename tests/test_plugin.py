import os

from pyblish import api, util, _plugin
from pyblish._vendor import mock
from nose.tools import (
    with_setup,
    assert_true,
    assert_equals,
    assert_raises,
    raises,
)

from . import lib


@with_setup(lib.setup_empty, lib.teardown)
def test_unique_id():
    """Plug-ins and instances have an id"""

    class MyPlugin(_plugin.Collector):
        pass

    class MyAction(_plugin.Action):
        pass

    assert_true(hasattr(MyPlugin, "id"))

    instance = _plugin.Instance("MyInstance")
    assert_true(hasattr(instance, "id"))

    # IDs are persistent
    assert_equals(instance.id, instance.id)
    assert_equals(MyAction.id, MyAction.id)
    assert_equals(MyPlugin.id, MyPlugin.id)

    context = _plugin.Context()
    assert_equals(context.id, context.id)

    # Even across discover()'s
    # Due to the fact that an ID is generated on module
    # load, which only happens once per process unless
    # module is forcefully reloaded by the user.
    api.register_plugin(MyPlugin)
    plugins = list(p for p in api.discover()
                   if p.id == MyPlugin.id)
    assert len(plugins) == 1, plugins
    assert plugins[0].__name__ == MyPlugin.__name__


def test_context_from_instance():
    """Instances provide access to their parent context"""

    context = _plugin.Context()
    instance = context.create_instance("MyInstance")
    assert_equals(context, instance.context)


def test_legacy():
    """Legacy is determined by existing process_* methods"""
    class LegacyPlugin(_plugin.Collector):
        def process_context(self, context):
            pass

    class NotLegacyPlugin(_plugin.Collector):
        def process(self, context):
            pass

    assert_true(hasattr(LegacyPlugin, "__pre11__"))
    assert_equals(LegacyPlugin.__pre11__, True)
    assert_true(hasattr(NotLegacyPlugin, "__pre11__"))
    assert_equals(NotLegacyPlugin.__pre11__, False)


def test_asset():
    """Using asset over instance works fine"""
    context = _plugin.Context()

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

    with lib.tempdir() as temp:
        print("Writing temporarily to: %s" % temp)
        module = os.path.join(temp, "selector.py")
        api.register_plugin_path(temp)

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
        plugins = [p.__name__ for p in api.discover()]

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
        plugins = [p.__name__ for p in api.discover()]

        assert "MyOtherSelector" in plugins, plugins
        assert "MySelector" not in plugins, plugins


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_unsupported_hosts():
    """Cannot register a unsupported plug-in in an unsupported host"""

    class Unsupported(api.Plugin):
        hosts = ["unsupported"]

    api.register_plugin(Unsupported)


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_unsupported_version():
    """Cannot register a plug-in of an unsupported version"""

    class Unsupported(api.Plugin):
        requires = (999, 999, 999)

    api.register_plugin(Unsupported)


@raises(TypeError)
@with_setup(lib.setup_empty, lib.teardown)
def test_register_malformed():
    """Cannot register a malformed plug-in"""

    class Unsupported(api.Plugin):
        families = True
        hosts = None

    api.register_plugin(Unsupported)


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

    with lib.tempdir() as d:
        api.register_plugin_path(d)

        with open(os.path.join(d, "discoverable.py"), "w") as f:
            f.write(discoverable)

        with open(os.path.join(d, "_undiscoverable.py"), "w") as f:
            f.write(notdiscoverable)

        plugins = [p.__name__ for p in api.discover()]
        assert "Discoverable" in plugins
        assert "NotDiscoverable" not in plugins


@with_setup(lib.setup_empty, lib.teardown)
def test_repair_context_backwardscompat():
    """Plug-ins with repair-context are reprogrammed appropriately"""

    class ValidateInstances(api.Validator):
        def repair_context(self, context):
            pass

    assert hasattr(ValidateInstances, "repair")
    assert not hasattr(ValidateInstances, "repair_context")


@with_setup(lib.setup_empty, lib.teardown)
def test_unique_logger():
    """A unique logger is applied to every plug-in"""

    count = {"#": 0}

    class MyPlugin(api.Plugin):
        def process(self, context):
            self.log.debug("Hello world")
            count["#"] += 1

    api.register_plugin(MyPlugin)

    context = util.publish()

    assert_equals(count["#"], 1)
    print(context.data("results"))

    results = context.data("results")[0]
    records = results["records"]
    hello_world = records[0]
    assert_equals(hello_world.msg, "Hello world")

    api.deregister_plugin(MyPlugin)


@with_setup(lib.setup_empty, lib.teardown)
def test_current_host():
    """api.current_host works"""
    _plugin.register_host("myhost")
    assert_equals(_plugin.current_host(), "myhost")

    assert_raises(Exception, _plugin.deregister_host, "notExist")


@with_setup(lib.setup_empty, lib.teardown)
def test_register_host():
    """Registering and deregistering hosts works fine"""
    _plugin.register_host("myhost")
    assert "myhost" in _plugin.registered_hosts()
    _plugin.deregister_host("myhost")
    assert "myhost" not in _plugin.registered_hosts()


@with_setup(lib.setup_empty, lib.teardown)
def test_current_target():
    """api.current_target works"""
    _plugin.register_target("mytarget")
    assert_equals(_plugin.current_target(), "mytarget")

    assert_raises(Exception, _plugin.deregister_target, "notExist")


@with_setup(lib.setup_empty, lib.teardown)
def test_current_target_latest():
    """api.current_target works"""
    _plugin.deregister_all_targets()
    _plugin.register_target("mytarget1")
    _plugin.register_target("mytarget2")
    assert_equals(_plugin.current_target(), "mytarget2")

    _plugin.register_target("mytarget1")
    assert_equals(_plugin.current_target(), "mytarget1")

    assert len(_plugin.registered_targets()) == 2


@with_setup(lib.setup_empty, lib.teardown)
def test_register_target():
    """Registering and deregistering targets works fine"""
    _plugin.register_target("mytarget")
    assert "mytarget" in _plugin.registered_targets()
    _plugin.deregister_target("mytarget")
    assert "mytarget" not in _plugin.registered_targets()


@with_setup(lib.setup_empty, lib.teardown)
def test_data_dict():
    """.data is a pure dictionary"""

    context = api.Context()
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

    class MyAction(_plugin.Action):
        def process(self, context):
            count["#"] += 1

    class MyPlugin(_plugin.Plugin):
        actions = [MyAction]

        def process(self, context):
            pass

    context = api.Context()
    _plugin.process(
        plugin=MyPlugin,
        context=context,
        action=MyAction.id)

    assert count["#"] == 1


@with_setup(lib.setup_empty, lib.teardown)
def test_actions():
    class MyAction(_plugin.Action):
        def process(self, context):
            context.data["key"] = "value"

    context = api.Context()
    _plugin.process(MyAction, context)
    assert "key" in context.data


@with_setup(lib.setup_empty, lib.teardown)
def test_action_error_checking():
    class MyActionValid(_plugin.Action):
        on = "all"

    class MyActionInvalid(_plugin.Action):
        on = "invalid"

    assert MyActionValid.__error__ is None
    assert MyActionInvalid.__error__


@with_setup(lib.setup_empty, lib.teardown)
def test_action_printing():
    class MyAction(_plugin.Action):
        pass

    my_action = MyAction()

    print(my_action)
    print(repr(my_action))

    assert str(my_action) == "MyAction"
    assert repr(my_action) == "pyblish._plugin.MyAction('MyAction')", (
        repr(my_action))


@with_setup(lib.setup_empty, lib.teardown)
def test_category_separator():
    assert issubclass(_plugin.Category("Test"),
                      _plugin.Action)
    assert issubclass(_plugin.Separator,
                      _plugin.Action)


def test_superclass_process_is_empty():
    """Superclass process() is empty"""
    def e():
        """Doc"""

    assert api.Plugin.process.__code__.co_code == e.__code__.co_code
    assert api.Plugin.repair.__code__.co_code == e.__code__.co_code


def test_plugin_source_path():
    """Plugins discovered carry a source path"""

    import sys
    plugin = _plugin.discover()[0]
    module = sys.modules[plugin.__module__]
    assert hasattr(module, "__file__")

    # Also works with inspect.getfile
    import inspect
    assert inspect.getfile(plugin) == module.__file__


@with_setup(lib.setup_empty, lib.teardown)
def test_register_callback():
    """Callback registration/deregistration works well"""

    def my_callback():
        pass

    def other_callback(data=None):
        pass

    _plugin.register_callback("mySignal", my_callback)

    msg = "Registering a callback failed"
    data = {"mySignal": [my_callback]}
    assert "mySignal" in _plugin.registered_callbacks() == data, msg

    _plugin.deregister_callback("mySignal", my_callback)

    assert_raises(
        ValueError,
        _plugin.deregister_callback,
        "mySignal", my_callback)

    assert_raises(
        KeyError,
        _plugin.deregister_callback,
        "notExist", my_callback)

    msg = "Deregistering a callback failed"
    data = {"mySignal": []}
    assert _plugin.registered_callbacks() == data, msg

    _plugin.register_callback("mySignal", my_callback)
    _plugin.register_callback("otherSignal", other_callback)
    _plugin.deregister_all_callbacks()

    msg = "Deregistering all callbacks failed"
    assert _plugin.registered_callbacks() == {}, msg


@with_setup(lib.setup_empty, lib.teardown)
def test_emit_signal_wrongly():
    """Exception from callback prints traceback"""

    def other_callback(an_argument=None):
        print("Ping from 'other_callback' with %s" % an_argument)

    _plugin.register_callback("otherSignal", other_callback)

    with lib.captured_stderr() as stderr:
        api.emit("otherSignal", not_an_argument="")
        output = stderr.getvalue().strip()
        print("Output: %s" % stderr.getvalue())
        assert output.startswith("Traceback")


@raises(ValueError)
@with_setup(lib.setup_empty, lib.teardown)
def test_registering_invalid_callback():
    """Can't register non-callables"""
    _plugin.register_callback("invalid", None)


@raises(KeyError)
def test_deregistering_nonexisting_callback():
    """Can't deregister a callback that doesn't exist"""
    _plugin.deregister_callback("invalid", lambda: "")


@raises(TypeError)
def test_register_noncallable_plugin():
    """Registered plug-ins must be callable"""
    _plugin.register_plugin("NotValid")


@raises(TypeError)
def test_register_old_plugin():
    """Can't register plug-ins incompatible with the version of Pyblish"""
    class MyPlugin(_plugin.Collector):
        requires = "pyblish==0"

    _plugin.register_plugin(MyPlugin)


@mock.patch("pyblish._plugin.__explicit_process")
def test_implicit_explicit_branching(func):
    """Explicit plug-ins are processed by the appropriate function"""

    # There are two mocks for this (see below); due to
    # @mock.patch.multiple being a dick.

    class Explicit(_plugin.ContextPlugin):
        pass

    util.publish(plugins=[Explicit])
    assert func.call_count == 1, func.call_count


@mock.patch("pyblish._plugin.__implicit_process")
def test_implicit_branching(func):
    """Implicit plug-ins are processed by the appropriate function"""

    class Implicit(_plugin.Plugin):
        pass

    util.publish(plugins=[Implicit])
    assert func.call_count == 1, func.call_count


def test_explicit_plugin():
    """ContextPlugin works as advertised"""

    count = {"#": 0}

    class Collector(_plugin.ContextPlugin):
        order = _plugin.CollectorOrder

        def process(self, context):
            self.log.info("Collecting from ContextPlugin")
            i = context.create_instance("MyInstance")
            i.data["family"] = "myFamily"
            count["#"] += 1

    class Validator(_plugin.InstancePlugin):
        order = _plugin.ValidatorOrder
        families = ["myFamily"]

        def process(self, instance):
            assert instance.data["name"] == "MyInstance", "fail"
            count["#"] += 10

    class ValidatorFailure(_plugin.InstancePlugin):
        order = _plugin.ValidatorOrder
        families = ["myFamily"]

        def process(self, instance):
            count["#"] += 100
            assert "notexist" in instance.data, "fail"

    class Extractor(_plugin.InstancePlugin):
        order = _plugin.ExtractorOrder
        families = ["myFamily"]

        def process(self, instance):
            count["#"] += 1000

    util.publish(
        plugins=[
            Collector,
            Validator,
            ValidatorFailure,
            Extractor
        ]
    )

    assert count["#"] == 111, count


def test_context_plugin_wrong_arguments():
    """ContextPlugin doesn't take wrong arguments well"""

    count = {"#": 0}

    class Collector(_plugin.InstancePlugin):
        def process(self, context, instance):
            print("I won't run")
            count["#"] += 1

    util.publish(plugins=[Collector])
    assert count["#"] == 0


def test_explicit_action():
    """Actions work with explicit plug-ins"""

    count = {"#": 0}

    class MyAction(_plugin.Action):
        def process(self, context):
            count["#"] += 1

    class MyPlugin(_plugin.ContextPlugin):
        actions = [MyAction]

        def process(self, context):
            pass

    context = api.Context()
    _plugin.process(
        plugin=MyPlugin,
        context=context,
        action=MyAction.id)


def test_explicit_results():
    """Explicit plug-ins contain results"""

    class Collector(_plugin.ContextPlugin):
        order = _plugin.CollectorOrder

        def process(self, context):
            self.log.info("logged")

    context = util.publish(plugins=[Collector])
    assert "results" in context.data

    result = context.data["results"][0]
    assert result["records"][0].msg == "logged"


def test_cooperative_collection():
    """Cooperative collection works

    A collector should be able to run such that the following
    collector "sees" the newly created instance so as to
    query and/or modify it.

    """

    count = {"#": 0}

    class CollectorA(api.Collector):
        order = 0.0

        def process(self, context):
            context.create_instance("myInstance")
            count["#"] += 1

    class CollectorB(api.Collector):
        order = 0.1

        def process(self, context):
            assert "myInstance" in [i.data["name"] for i in context]

            # This should run
            count["#"] += 10

    api.register_plugin(CollectorA)
    api.register_plugin(CollectorB)

    util.publish()

    assert count["#"] == 11, count


def test_actions_and_explicit_plugins():
    """Actions work with explicit plug-ins"""

    count = {"#": 0}

    class MyAction(api.Action):
        def process(self, context, plugin):
            count["#"] += 1
            raise Exception("Errored")

    class MyValidator(api.InstancePlugin):
        order = api.ValidatorOrder

        actions = [
            api.Category("Scene"),
            MyAction
        ]

        def process(self, instance):
            count["#"] += 10

    context = api.Context()
    result = _plugin.process(MyValidator,
                             context,
                             instance=None,
                             action=MyAction.id)
    assert count["#"] == 1
    assert str(result["error"]) == "Errored", result


@with_setup(lib.setup_empty, lib.teardown)
def test_argumentless_plugin():
    """Plug-ins with neither instance nor context should still run"""
    count = {"#": 0}

    class MyPlugin(api.Validator):
        def process(self):
            count["#"] += 1

    api.register_plugin(MyPlugin)
    util.publish()

    assert count["#"] == 1


@with_setup(lib.setup_empty, lib.teardown)
def test_argumentless_explitic_plugin():
    """Explicit plug-ins, without arguments, should fail"""
    class MyPlugin(api.InstancePlugin):
        def process(self):
            pass

    raises(TypeError, api.register_plugin, MyPlugin)

    class MyPlugin(api.ContextPlugin):
        def process(self):
            pass

    raises(TypeError, api.register_plugin, MyPlugin)


@with_setup(lib.setup_empty, lib.teardown)
def test_changes_to_registered_plugins_are_not_persistent():
    """Changes to registerd plug-ins do not persist

    This is the expected behaviour of file-based plug-ins.

    """

    class MyPlugin(api.ContextPlugin):
        active = False

    api.register_plugin(MyPlugin)

    registered = api.registered_plugins()[0]
    assert registered.id == MyPlugin.id
    assert registered.active is False

    registered.active = True
    assert registered.active is True

    registered = api.registered_plugins()[0]
    assert registered.active is False
