import os
import contextlib

# Local library
from . import lib

from pyblish import api, logic, plugin, util

from nose.tools import (
    with_setup,
    assert_equals,
)


@contextlib.contextmanager
def no_guis():
    os.environ.pop("PYBLISHGUI", None)
    for gui in logic.registered_guis():
        logic.deregister_gui(gui)

    yield


@with_setup(lib.setup, lib.teardown)
def test_iterator():
    """Iterator skips inactive plug-ins and instances"""

    count = {"#": 0}

    class MyCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            inactive = context.create_instance("Inactive")
            active = context.create_instance("Active")

            inactive.data["publish"] = False
            active.data["publish"] = True

            count["#"] += 1

    class MyValidatorA(api.InstancePlugin):
        order = api.ValidatorOrder
        active = False

        def process(self, instance):
            count["#"] += 10

    class MyValidatorB(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            count["#"] += 100

    context = api.Context()
    plugins = [MyCollector, MyValidatorA, MyValidatorB]

    assert count["#"] == 0, count

    for Plugin, instance in logic.Iterator(plugins, context):
        assert instance.name != "Inactive" if instance else True
        assert Plugin.__name__ != "MyValidatorA"

        plugin.process(Plugin, context, instance)

    # Collector runs once, one Validator runs once
    assert count["#"] == 101, count


def test_iterator_with_explicit_targets():
    """Iterator skips non-targeted plug-ins"""

    count = {"#": 0}

    class MyCollectorA(api.ContextPlugin):
        order = api.CollectorOrder
        targets = ["studio"]

        def process(self, context):
            count["#"] += 1

    class MyCollectorB(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            count["#"] += 10

    class MyCollectorC(api.ContextPlugin):
        order = api.CollectorOrder
        targets = ["studio"]

        def process(self, context):
            count["#"] += 100

    context = api.Context()
    plugins = [MyCollectorA, MyCollectorB, MyCollectorC]

    assert count["#"] == 0, count

    for Plugin, instance in logic.Iterator(
        plugins, context, targets=["studio"]
    ):
        assert Plugin.__name__ != "MyCollectorB"

        plugin.process(Plugin, context, instance)

    # Collector runs once, one Validator runs once
    assert count["#"] == 101, count


def test_register_gui():
    """Registering at run-time takes precedence over those from environment"""

    with no_guis():
        os.environ["PYBLISHGUI"] = "second,third"
        logic.register_gui("first")

        print(logic.registered_guis())
        assert logic.registered_guis() == ["first", "second", "third"]

    with no_guis():
        os.environ["PYBLISH_GUI"] = "second,third"
        logic.register_gui("first")

        print(logic.registered_guis())
        assert logic.registered_guis() == ["first", "second", "third"]


@with_setup(lib.setup_empty, lib.teardown)
def test_subset_match():
    """Plugin.match = api.Subset works as expected"""

    count = {"#": 0}

    class MyPlugin(api.InstancePlugin):
        families = ["a", "b"]
        match = api.Subset

        def process(self, instance):
            count["#"] += 1

    context = api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("included_1", families=["a", "b"])
    context.create_instance("included_2", families=["a", "b", "c"])

    util.publish(context, plugins=[MyPlugin])

    assert_equals(count["#"], 2)

    instances = logic.instances_by_plugin(context, MyPlugin)
    assert_equals(list(i.name for i in instances),
                  ["included_1", "included_2"])


def test_subset_exact():
    """Plugin.match = api.Exact works as expected"""

    count = {"#": 0}

    class MyPlugin(api.InstancePlugin):
        families = ["a", "b"]
        match = api.Exact

        def process(self, instance):
            count["#"] += 1

    context = api.Context()

    context.create_instance("not_included_1", families=["a"])
    context.create_instance("not_included_1", families=["x"])
    context.create_instance("not_included_3", families=["a", "b", "c"])
    instance = context.create_instance("included_1", families=["a", "b"])

    # Discard the solo-family member, which defaults to `default`.
    #
    # When using multiple families, it is common not to bother modifying
    # `family`, and in the future this member needn't be there at all and
    # may/should be removed. But till then, for complete clarity, it might
    # be worth removing this explicitly during the creation of instances
    # if instead choosing to use the `families` key.
    instance.data.pop("family")

    util.publish(context, plugins=[MyPlugin])

    assert_equals(count["#"], 1)

    instances = logic.instances_by_plugin(context, MyPlugin)
    assert_equals(list(i.name for i in instances), ["included_1"])


def test_plugins_by_families():
    """The right plug-ins are returned from plugins_by_families"""

    class ClassA(api.Collector):
        families = ["a"]

    class ClassB(api.Collector):
        families = ["b"]

    class ClassC(api.Collector):
        families = ["c"]

    class ClassD(api.Collector):
        families = ["a", "b"]
        match = api.Intersection

    class ClassE(api.Collector):
        families = ["a", "b"]
        match = api.Subset

    class ClassF(api.Collector):
        families = ["a", "b"]
        match = api.Exact

    assert logic.plugins_by_families(
        [ClassA, ClassB, ClassC], ["a", "z"]) == [ClassA]

    assert logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a"]) == [ClassD]

    assert logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a", "b"]) == [ClassD, ClassE, ClassF]

    assert logic.plugins_by_families(
        [ClassD, ClassE, ClassF], ["a", "b", "c"]) == [ClassD, ClassE]


@with_setup(lib.setup_empty, lib.teardown)
def test_extracted_traceback_contains_correct_backtrace():
    api.register_plugin_path(os.path.dirname(__file__))

    context = api.Context()
    context.create_instance('test instance')

    plugins = api.discover()
    plugins = [p for p in plugins if p.__name__ in
               ('FailingExplicitPlugin', 'FailingImplicitPlugin')]
    util.publish(context, plugins)

    for result in context.data['results']:
        assert result["error"].traceback[0] == plugins[0].__module__
        formatted_tb = result['error'].formatted_traceback
        assert formatted_tb.startswith('Traceback (most recent call last):\n')
        assert formatted_tb.endswith('\nException: A test exception\n')
        assert 'File "{0}",'.format(plugins[0].__module__) in formatted_tb
