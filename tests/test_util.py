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
    util._convenience(plugins=[PluginB], order=0.5)

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


@with_setup(lib.setup, lib.teardown)
def test_publishing_explicit_targets():
    """Publishing with explicit targets works"""

    count = {"#": 0}

    class plugin(api.ContextPlugin):
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(plugin)

    util.publish(targets=["custom"])

    assert count["#"] == 1, count


def test_publishing_explicit_targets_with_global():
    """Publishing with explicit and globally registered targets works"""

    count = {"#": 0}

    class Plugin1(api.ContextPlugin):
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    class Plugin2(api.ContextPlugin):
        targets = ["foo"]

        def process(self, context):
            count["#"] += 10

    api.register_target("foo")
    api.register_target("custom")
    api.register_plugin(Plugin1)
    api.register_plugin(Plugin2)

    util.publish(targets=["custom"])

    assert count["#"] == 1, count
    assert api.registered_targets() == ["foo", "custom"]

    api.deregister_all_targets()


@with_setup(lib.setup, lib.teardown)
def test_per_session_targets():
    """Register targets per session works"""

    util.publish(targets=["custom"])

    registered_targets = api.registered_targets()
    assert registered_targets == [], registered_targets


@with_setup(lib.setup, lib.teardown)
def test_publishing_collectors():
    """Running collectors with targets works"""

    count = {"#": 0}

    class plugin(api.ContextPlugin):
        order = api.CollectorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(plugin)

    util.collect(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup, lib.teardown)
def test_publishing_validators():
    """Running validators with targets works"""

    count = {"#": 0}

    class plugin(api.ContextPlugin):
        order = api.ValidatorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(plugin)

    util.validate(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup, lib.teardown)
def test_publishing_extractors():
    """Running extractors with targets works"""

    count = {"#": 0}

    class plugin(api.ContextPlugin):
        order = api.ExtractorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(plugin)

    util.extract(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup, lib.teardown)
def test_publishing_integrators():
    """Running integrators with targets works"""

    count = {"#": 0}

    class plugin(api.ContextPlugin):
        order = api.IntegratorOrder
        targets = ["custom"]

        def process(self, context):
            count["#"] += 1

    api.register_plugin(plugin)

    util.integrate(targets=["custom"])

    assert count["#"] == 1, count


@with_setup(lib.setup, lib.teardown)
def test_progress_existence():
    """Progress data member exists"""

    class plugin(api.ContextPlugin):
        pass

    api.register_plugin(plugin)

    result = next(util.publish_iter())

    assert "progress" in result, result


@with_setup(lib.setup, lib.teardown)
def test_publish_iter_increment_progress():
    """Publish iteration increments progress"""

    class pluginA(api.ContextPlugin):
        pass

    class pluginB(api.ContextPlugin):
        pass

    api.register_plugin(pluginA)
    api.register_plugin(pluginB)

    iterator = util.publish_iter()

    pluginA_progress = next(iterator)["progress"]
    pluginB_progress = next(iterator)["progress"]

    assert pluginA_progress < pluginB_progress
