import os
import logging

from pyblish.vendor import mock
import pyblish.api
import pyblish.util
import pyblish.plugin
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

    class MyPlugin(pyblish.plugin.Collector):
        pass

    class MyAction(pyblish.plugin.Action):
        pass

    assert_true(hasattr(MyPlugin, "id"))

    instance = pyblish.plugin.Instance("MyInstance")
    assert_true(hasattr(instance, "id"))

    # IDs are persistent
    assert_equals(instance.id, instance.id)
    assert_equals(MyAction.id, MyAction.id)
    assert_equals(MyPlugin.id, MyPlugin.id)

    context = pyblish.plugin.Context()
    assert_equals(context.id, context.id)

    # Even across discover()'s
    # Due to the fact that an ID is generated on module
    # load, which only happens once per process unless
    # module is forcefully reloaded by the user.
    pyblish.api.register_plugin(MyPlugin)
    plugins = list(p for p in pyblish.api.discover()
                   if p.id == MyPlugin.id)
    assert len(plugins) == 1, plugins
    assert plugins[0].__name__ == MyPlugin.__name__


def test_context_from_instance():
    """Instances provide access to their parent context"""

    context = pyblish.plugin.Context()
    instance = context.create_instance("MyInstance")
    assert_equals(context, instance.context)


def test_legacy():
    """Legacy is determined by existing process_* methods"""
    class LegacyPlugin(pyblish.plugin.Collector):
        def process_context(self, context):
            pass

    class NotLegacyPlugin(pyblish.plugin.Collector):
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

    with lib.tempdir() as temp:
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

    with lib.tempdir() as d:
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
    print(context.data("results"))

    results = context.data("results")[0]
    records = results["records"]
    hello_world = records[0]
    assert_equals(hello_world.msg, "Hello world")

    pyblish.api.deregister_plugin(MyPlugin)


@with_setup(lib.setup_empty, lib.teardown)
def test_current_host():
    """pyblish.api.current_host works"""
    pyblish.plugin.register_host("myhost")
    assert_equals(pyblish.plugin.current_host(), "myhost")

    assert_raises(Exception, pyblish.plugin.deregister_host, "notExist")


@with_setup(lib.setup_empty, lib.teardown)
def test_register_host():
    """Registering and deregistering hosts works fine"""
    pyblish.plugin.register_host("myhost")
    assert "myhost" in pyblish.plugin.registered_hosts()
    pyblish.plugin.deregister_host("myhost")
    assert "myhost" not in pyblish.plugin.registered_hosts()


@with_setup(lib.setup_empty, lib.teardown)
def test_current_target():
    """pyblish.api.current_target works"""
    pyblish.plugin.register_target("mytarget")
    assert_equals(pyblish.plugin.current_target(), "mytarget")

    assert_raises(Exception, pyblish.plugin.deregister_target, "notExist")


@with_setup(lib.setup_empty, lib.teardown)
def test_current_target_latest():
    """pyblish.api.current_target works"""
    pyblish.plugin.deregister_all_targets()
    pyblish.plugin.register_target("mytarget1")
    pyblish.plugin.register_target("mytarget2")
    assert_equals(pyblish.plugin.current_target(), "mytarget2")

    pyblish.plugin.register_target("mytarget1")
    assert_equals(pyblish.plugin.current_target(), "mytarget1")

    assert len(pyblish.plugin.registered_targets()) == 2


@with_setup(lib.setup_empty, lib.teardown)
def test_register_target():
    """Registering and deregistering targets works fine"""
    pyblish.plugin.register_target("mytarget")
    assert "mytarget" in pyblish.plugin.registered_targets()
    pyblish.plugin.deregister_target("mytarget")
    assert "mytarget" not in pyblish.plugin.registered_targets()


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
        action=MyAction.id)

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
    print(repr(MyAction()))

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
def test_register_callback():
    """Callback registration/deregistration works well"""

    def my_callback():
        pass

    def other_callback(data=None):
        pass

    pyblish.plugin.register_callback("mySignal", my_callback)

    msg = "Registering a callback failed"
    data = {"mySignal": [my_callback]}
    assert "mySignal" in pyblish.plugin.registered_callbacks() == data, msg

    pyblish.plugin.deregister_callback("mySignal", my_callback)

    assert_raises(
        ValueError,
        pyblish.plugin.deregister_callback,
        "mySignal", my_callback)

    assert_raises(
        KeyError,
        pyblish.plugin.deregister_callback,
        "notExist", my_callback)

    msg = "Deregistering a callback failed"
    data = {"mySignal": []}
    assert pyblish.plugin.registered_callbacks() == data, msg

    pyblish.plugin.register_callback("mySignal", my_callback)
    pyblish.plugin.register_callback("otherSignal", other_callback)
    pyblish.plugin.deregister_all_callbacks()

    msg = "Deregistering all callbacks failed"
    assert pyblish.plugin.registered_callbacks() == {}, msg


@with_setup(lib.setup_empty, lib.teardown)
def test_emit_signal_wrongly():
    """Exception from callback prints traceback"""

    def other_callback(an_argument=None):
        print("Ping from 'other_callback' with %s" % an_argument)

    pyblish.plugin.register_callback("otherSignal", other_callback)

    with lib.captured_stderr() as stderr:
        pyblish.lib.emit("otherSignal", not_an_argument="")
        output = stderr.getvalue().strip()
        print("Output: %s" % stderr.getvalue())
        assert output.startswith("Traceback")


@raises(ValueError)
@with_setup(lib.setup_empty, lib.teardown)
def test_registering_invalid_callback():
    """Can't register non-callables"""
    pyblish.plugin.register_callback("invalid", None)


@raises(KeyError)
def test_deregistering_nonexisting_callback():
    """Can't deregister a callback that doesn't exist"""
    pyblish.plugin.deregister_callback("invalid", lambda: "")


@raises(TypeError)
def test_register_noncallable_plugin():
    """Registered plug-ins must be callable"""
    pyblish.plugin.register_plugin("NotValid")


@raises(TypeError)
def test_register_old_plugin():
    """Can't register plug-ins incompatible with the version of Pyblish"""
    class MyPlugin(pyblish.plugin.Collector):
        requires = "pyblish==0"

    pyblish.plugin.register_plugin(MyPlugin)


@mock.patch("pyblish.plugin.__explicit_process")
def test_implicit_explicit_branching(func):
    """Explicit plug-ins are processed by the appropriate function"""

    # There are two mocks for this (see below); due to
    # @mock.patch.multiple being a dick.

    class Explicit(pyblish.plugin.ContextPlugin):
        pass

    pyblish.util.publish(plugins=[Explicit])
    assert func.call_count == 1, func.call_count


@mock.patch("pyblish.plugin.__implicit_process")
def test_implicit_branching(func):
    """Implicit plug-ins are processed by the appropriate function"""

    class Implicit(pyblish.plugin.Plugin):
        pass

    pyblish.util.publish(plugins=[Implicit])
    assert func.call_count == 1, func.call_count


def test_explicit_plugin():
    """ContextPlugin works as advertised"""

    count = {"#": 0}

    class Collector(pyblish.plugin.ContextPlugin):
        order = pyblish.plugin.CollectorOrder

        def process(self, context):
            self.log.info("Collecting from ContextPlugin")
            i = context.create_instance("MyInstance")
            i.data["family"] = "myFamily"
            count["#"] += 1

    class Validator(pyblish.plugin.InstancePlugin):
        order = pyblish.plugin.ValidatorOrder
        families = ["myFamily"]

        def process(self, instance):
            assert instance.data["name"] == "MyInstance", "fail"
            count["#"] += 10

    class ValidatorFailure(pyblish.plugin.InstancePlugin):
        order = pyblish.plugin.ValidatorOrder
        families = ["myFamily"]

        def process(self, instance):
            count["#"] += 100
            assert "notexist" in instance.data, "fail"

    class Extractor(pyblish.plugin.InstancePlugin):
        order = pyblish.plugin.ExtractorOrder
        families = ["myFamily"]

        def process(self, instance):
            count["#"] += 1000

    pyblish.util.publish(
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

    class Collector(pyblish.plugin.InstancePlugin):
        def process(self, context, instance):
            print("I won't run")
            count["#"] += 1

    pyblish.util.publish(plugins=[Collector])
    assert count["#"] == 0


def test_explicit_action():
    """Actions work with explicit plug-ins"""

    count = {"#": 0}

    class MyAction(pyblish.plugin.Action):
        def process(self, context):
            count["#"] += 1

    class MyPlugin(pyblish.plugin.ContextPlugin):
        actions = [MyAction]

        def process(self, context):
            pass

    context = pyblish.api.Context()
    pyblish.plugin.process(
        plugin=MyPlugin,
        context=context,
        action=MyAction.id)


def test_explicit_results():
    """Explicit plug-ins contain results"""

    class Collector(pyblish.plugin.ContextPlugin):
        order = pyblish.plugin.CollectorOrder

        def process(self, context):
            self.log.info("logged")

    context = pyblish.util.publish(plugins=[Collector])
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

    class CollectorA(pyblish.api.Collector):
        order = 0.0

        def process(self, context):
            context.create_instance("myInstance")
            count["#"] += 1

    class CollectorB(pyblish.api.Collector):
        order = 0.1

        def process(self, context):
            assert "myInstance" in [i.data["name"] for i in context]

            # This should run
            count["#"] += 10

    pyblish.api.register_plugin(CollectorA)
    pyblish.api.register_plugin(CollectorB)

    pyblish.util.publish()

    assert count["#"] == 11, count


def test_actions_and_explicit_plugins():
    """Actions work with explicit plug-ins"""

    count = {"#": 0}

    class MyAction(pyblish.api.Action):
        def process(self, context, plugin):
            count["#"] += 1
            raise Exception("Errored")

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        actions = [
            pyblish.api.Category("Scene"),
            MyAction
        ]

        def process(self, instance):
            count["#"] += 10

    context = pyblish.api.Context()
    result = pyblish.plugin.process(MyValidator,
                                    context,
                                    instance=None,
                                    action=MyAction.id)
    assert count["#"] == 1
    assert str(result["error"]) == "Errored", result


@with_setup(lib.setup_empty, lib.teardown)
def test_argumentless_plugin():
    """Plug-ins with neither instance nor context should still run"""
    count = {"#": 0}

    class MyPlugin(pyblish.api.Validator):
        def process(self):
            count["#"] += 1

    pyblish.api.register_plugin(MyPlugin)
    pyblish.util.publish()

    assert count["#"] == 1


@with_setup(lib.setup_empty, lib.teardown)
def test_argumentless_explitic_plugin():
    """Explicit plug-ins, without arguments, should fail"""
    class MyPlugin(pyblish.api.InstancePlugin):
        def process(self):
            pass

    raises(TypeError, pyblish.api.register_plugin, MyPlugin)

    class MyPlugin(pyblish.api.ContextPlugin):
        def process(self):
            pass

    raises(TypeError, pyblish.api.register_plugin, MyPlugin)


@with_setup(lib.setup_empty, lib.teardown)
def test_changes_to_registered_plugins_are_not_persistent():
    """Changes to registered plug-ins do not persist

    This is the expected behaviour of file-based plug-ins.

    """

    class MyPlugin(pyblish.api.ContextPlugin):
        active = False

    pyblish.api.register_plugin(MyPlugin)

    registered = pyblish.api.registered_plugins()[0]
    assert registered.id == MyPlugin.id
    assert registered.active is False

    registered.active = True
    assert registered.active is True

    registered = pyblish.api.registered_plugins()[0]
    assert registered.active is False


@with_setup(lib.setup_empty, lib.teardown)
def test_logging_solely_from_pyblish():
    """Only logging calls with self.log should be recorded."""

    class collect(pyblish.api.ContextPlugin):

        def process(self, context):
            import logging
            log = logging.getLogger("temp_logger")
            log.info("I should not be recorded!")

    context = pyblish.util.publish(plugins=[collect])
    for result in context.data["results"]:
        for record in result["records"]:
            assert record.name.startswith("pyblish")


@with_setup(lib.setup_empty, lib.teardown)
def test_running_for_all_targets():
    """Run for all targets when family is "default"."""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):

        targets = ["default"]

        def process(self, context):
            count["#"] += 1

    pyblish.util.publish(plugins=[plugin])

    assert count["#"] == 1, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_dont_run_non_matching_targets():
    """Don't run plugins that haven't got a target registered."""

    count = {"#": 0}

    class plugin(pyblish.api.ContextPlugin):

        targets = ["studio"]

        def process(self, context):
            count["#"] += 1

    pyblish.util.publish(plugins=[plugin])

    assert count["#"] == 0, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_only_run_plugins_that_match_registered_targets():
    """Only run plugins that match the registered targets."""

    count = {"#": 0}

    class pluginStudio(pyblish.api.ContextPlugin):

        targets = ["studio"]

        def process(self, context):
            count["#"] += 1

    class pluginProject(pyblish.api.ContextPlugin):

        targets = ["project"]

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_target("studio")
    pyblish.util.publish(plugins=[pluginStudio, pluginProject])

    assert count["#"] == 1, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_targets_and_exact_matching():
    """Run targets with exact matching."""

    count = {"#": 0}

    class pluginStudio(pyblish.api.ContextPlugin):

        targets = ["default", "studio"]
        match = pyblish.api.Exact

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_target("studio")
    pyblish.util.publish(plugins=[pluginStudio])

    assert count["#"] == 1, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_targets_and_subset_matching():
    """Run targets with subset matching."""

    count = {"#": 0}

    class pluginStudio(pyblish.api.ContextPlugin):

        targets = ["studio"]
        match = pyblish.api.Subset

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_target("studio")
    pyblish.util.publish(plugins=[pluginStudio])

    assert count["#"] == 1, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_targets_and_publishing():
    """Only run plugins with requested targets."""

    count = {"#": 0}

    class pluginA(pyblish.api.ContextPlugin):

        targets = ["customA"]

        def process(self, context):
            count["#"] += 1

    class pluginB(pyblish.api.ContextPlugin):

        def process(self, context):
            count["#"] += 1

    pyblish.util.publish(plugins=[pluginA, pluginB], targets=["customA"])

    assert count["#"] == 1, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_targets_and_publishing_with_default():
    """Only run plugins with requested targets including default."""

    count = {"#": 0}

    class pluginA(pyblish.api.ContextPlugin):

        targets = ["customA"]

        def process(self, context):
            count["#"] += 1

    class pluginB(pyblish.api.ContextPlugin):

        def process(self, context):
            count["#"] += 1

    pyblish.util.publish(
        plugins=[pluginA, pluginB], targets=["default", "customA"]
    )

    assert count["#"] == 2, "count is {0}".format(count)


@with_setup(lib.setup_empty, lib.teardown)
def test_duplicate_plugin_names():
    logging.basicConfig(level=logging.DEBUG)

    pyblish.plugin.ALLOW_DUPLICATES = True

    plugins = []
    with lib.tempdir() as temp:
        plugin = (
            "from pyblish import api\nclass collectorA(api.ContextPlugin):"
            "\n    def process(self, context):\n        pass"
        )
        path = os.path.join(temp, "pluginA.py")
        with open(path, "w") as the_file:
            the_file.write(plugin)

        path = os.path.join(temp, "pluginA_copy.py")
        with open(path, "w") as the_file:
            the_file.write(plugin)

        plugins.extend(pyblish.api.discover(paths=[temp]))

    assert len(plugins) == 2, plugins

    # Restore state, for subsequent tests
    # NOTE: This assumes the test succeeds. If it fails, then
    # subsequent tests can fail because of it.
    pyblish.plugin.ALLOW_DUPLICATES = False


@with_setup(lib.setup_empty, lib.teardown)
def test_validate_publish_data_member_type():
    """Validate publish data member type works."""

    pyblish.plugin.STRICT_DATATYPES = True

    cxt = pyblish.api.Context()
    instance = cxt.create_instance(name="A")
    try:
        instance.data["publish"] = 1.0
    except TypeError:
        instance.data["publish"] = True

    msg = "\"publish\" data member on \"{0}\" is not a boolean.".format(
        instance
    )
    assert isinstance(instance.data.get("publish", True), bool), msg

    # Restore state, for subsequent tests
    # NOTE: This assumes the test succeeds. If it fails, then
    # subsequent tests can fail because of it.
    pyblish.plugin.STRICT_DATATYPES = False


@with_setup(lib.setup_empty, lib.teardown)
def test_discovery_filter():
    """Plugins can be filtered and modified"""

    class MyFilteredPlugin(pyblish.plugin.Collector):
        pass

    class MyModifiedPlugin(pyblish.plugin.Validator):
        optional = False

    def my_plugin_filter(plugins):
        for plugin in list(plugins):

            # Plug-ins can be removed..
            if plugin.__name__ == "MyFilteredPlugin":
                plugins.remove(plugin)

            # ..and modified
            if plugin.__name__ == "MyModifiedPlugin":
                plugin.optional = True

    pyblish.api.register_plugin(MyFilteredPlugin)
    pyblish.api.register_plugin(MyModifiedPlugin)
    pyblish.api.register_discovery_filter(my_plugin_filter)
    plugins = pyblish.api.discover()
    assert len(plugins) == 1, plugins
    assert plugins[0].__name__ == MyModifiedPlugin.__name__
    assert plugins[0].optional is True


@with_setup(lib.setup_empty, lib.teardown)
def test_deregister_discovery():
    """Test discovery filters can be deregistered"""
    class MyFilteredPlugin(pyblish.plugin.Collector):
        pass

    def my_plugin_filter(plugins):
        for plugin in list(plugins):
            if plugin.__name__ == "MyFilteredPlugin":
                plugins.remove(plugin)

    pyblish.api.register_plugin(MyFilteredPlugin)
    pyblish.api.register_discovery_filter(my_plugin_filter)
    plugins = pyblish.api.discover()
    assert len(plugins) == 0, plugins
    pyblish.api.register_plugin(MyFilteredPlugin)
    pyblish.api.deregister_discovery_filter(my_plugin_filter)
    plugins = pyblish.api.discover()
    assert len(plugins) == 1, plugins


@with_setup(lib.setup_empty, lib.teardown)
def test_discovering_unicode_contained_plugin():
    unicode_plugin = b"""
import pyblish.api

class UnicodePlugin(pyblish.api.InstancePlugin):
    label = "\xf0\x9f\xa4\xa8"
"""

    with lib.tempdir() as d:
        pyblish.api.register_plugin_path(d)

        with open(os.path.join(d, "unicode_plugin.py"), "wb") as f:
            f.write(unicode_plugin)

        plugins = [p.__name__ for p in pyblish.api.discover()]
        assert plugins == ["UnicodePlugin"]


def test_sort_plugins():
    """Ensure that plugins order is correct."""
    pyblish.plugin.SORT_PER_ORDER_AND_TYPE = True

    class Plugin2(pyblish.plugin.InstancePlugin):
        order = 1

    class Plugin1(pyblish.plugin.ContextPlugin):
        order = 1

    class Plugin3(pyblish.plugin.ContextPlugin):
        order = 2

    plugins = [Plugin3, Plugin2, Plugin1]
    pyblish.plugin.sort(plugins)
    assert plugins == [Plugin1, Plugin2, Plugin3]

    # Restore state, for subsequent tests
    # NOTE: This assumes the test succeeds. If it fails, then
    # subsequent tests can fail because of it.
    pyblish.plugin.SORT_PER_ORDER_AND_TYPE = False

