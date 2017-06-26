import os

from . import lib

from pyblish import api, util
from nose.tools import (
    with_setup
)


def test_convenience_plugins_argument():
    """util._convenience() `plugins` argument works

    Issue: #286

    """

    count = {"#": 0}

    class PluginA(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            count["#"] += 1

    class PluginB(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            count["#"] += 10

    assert count["#"] == 0

    api.register_plugin(PluginA)
    util._convenience(0.5, plugins=[PluginB])

    assert count["#"] == 10, count


@with_setup(lib.setup, lib.teardown)
def test_convenience_functions():
    """convenience functions works as expected"""

    count = {"#": 0}

    class Collector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class Validator(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    class Extractor(api.InstancePlugin):
        order = api.ExtractorOrder

        def process(self, instance):
            count["#"] += 100

    class Integrator(api.ContextPlugin):
        order = api.IntegratorOrder

        def process(self, instance):
            count["#"] += 1000

    class PostIntegrator(api.ContextPlugin):
        order = api.IntegratorOrder + 0.1

        def process(self, instance):
            count["#"] += 10000

    class NotCVEI(api.ContextPlugin):
        """This plug-in is too far away from Integration to qualify as CVEI"""
        order = api.IntegratorOrder + 2.0

        def process(self, instance):
            count["#"] += 100000

    assert count["#"] == 0

    for Plugin in (Collector,
                   Validator,
                   Extractor,
                   Integrator,
                   PostIntegrator,
                   NotCVEI):
        api.register_plugin(Plugin)

    context = util.collect()

    assert count["#"] == 1

    util.validate(context)

    assert count["#"] == 11

    util.extract(context)

    assert count["#"] == 111

    util.integrate(context)

    assert count["#"] == 11111


@with_setup(lib.setup, lib.teardown)
def test_multiple_instance_util_publish():
    """Multiple instances work with util.publish()

    This also ensures it operates correctly with an
    InstancePlugin collector.

    """

    count = {"#": 0}

    class MyContextCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            context.create_instance("A")
            context.create_instance("B")
            count["#"] += 1

    class MyInstancePluginCollector(api.InstancePlugin):
        order = api.CollectorOrder + 0.1

        def process(self, instance):
            count["#"] += 1

    api.register_plugin(MyContextCollector)
    api.register_plugin(MyInstancePluginCollector)

    # Ensure it runs without errors
    util.publish()

    assert count["#"] == 3


@with_setup(lib.setup, lib.teardown)
def test_modify_context_during_CVEI():
    """Custom logic made possible via convenience members"""

    count = {"#": 0}

    class MyCollector(api.ContextPlugin):
        order = api.CollectorOrder

        def process(self, context):
            camera = context.create_instance("MyCamera")
            model = context.create_instance("MyModel")

            camera.data["family"] = "camera"
            model.data["family"] = "model"

            count["#"] += 1

    class MyValidator(api.InstancePlugin):
        order = api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    api.register_plugin(MyCollector)
    api.register_plugin(MyValidator)

    context = api.Context()

    assert count["#"] == 0, count

    util.collect(context)

    assert count["#"] == 1, count

    context[:] = filter(lambda i: i.data["family"] == "camera", context)

    util.validate(context)

    # Only model remains
    assert count["#"] == 11, count

    # No further processing occurs.
    util.extract(context)
    util.integrate(context)

    assert count["#"] == 11, count


@with_setup(lib.setup, lib.teardown)
def test_environment_host_registration():
    """Host registration from PYBLISH_HOSTS works"""

    count = {"#": 0}
    hosts = ["test1", "test2"]

    # Test single hosts
    class SingleHostCollector(api.ContextPlugin):
        order = api.CollectorOrder
        host = hosts[0]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(SingleHostCollector)

    context = api.Context()

    os.environ["PYBLISH_HOSTS"] = "test1"
    util.collect(context)

    assert count["#"] == 1, count

    # Test multiple hosts
    api.deregister_all_plugins()

    class MultipleHostsCollector(api.ContextPlugin):
        order = api.CollectorOrder
        host = hosts

        def process(self, context):
            count["#"] += 10

    api.register_plugin(MultipleHostsCollector)

    context = api.Context()

    os.environ["PYBLISH_HOSTS"] = os.pathsep.join(hosts)
    util.collect(context)

    assert count["#"] == 11, count
