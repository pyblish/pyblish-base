
# Local library
from . import lib

from pyblish import api, logic, plugin

from nose.tools import (
    with_setup
)


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
