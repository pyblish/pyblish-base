from . import lib

import pyblish.api
import pyblish.lib
import pyblish.util
import pyblish.compat
from nose.tools import (
    with_setup
)


def test_convenience_plugins_argument():
    """util._convenience() `plugins` argument works
    
    Issue: #286
    
    """

    count = {"#": 0}

    class PluginA(pyblish.api.ContextPlugin):
      order = pyblish.api.CollectorOrder
    
      def process(self, context):
        count["#"] += 1

    class PluginB(pyblish.api.ContextPlugin):
      order = pyblish.api.CollectorOrder

      def process(self, context):
        count["#"] += 10

    assert count["#"] == 0

    pyblish.api.register_plugin(PluginA)
    pyblish.util._convenience(0.5, plugins=[PluginB])

    assert count["#"] == 10, count


@with_setup(lib.setup, lib.teardown)
def test_convenience_functions():
    """convenience functions works as expected"""

    count = {"#": 0}

    class Collector(pyblish.plugin.ContextPlugin):
        order = pyblish.plugin.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class Validator(pyblish.plugin.InstancePlugin):
        order = pyblish.plugin.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    class Extractor(pyblish.plugin.InstancePlugin):
        order = pyblish.plugin.ExtractorOrder

        def process(self, instance):
            count["#"] += 100

    class Integrator(pyblish.plugin.ContextPlugin):
        order = pyblish.plugin.IntegratorOrder

        def process(self, instance):
            count["#"] += 1000

    class PostIntegrator(pyblish.plugin.ContextPlugin):
        order = pyblish.plugin.IntegratorOrder + 0.5

        def process(self, instance):
            count["#"] += 10000

    assert count["#"] == 0
    
    for Plugin in (Collector,
                   Validator,
                   Extractor,
                   Integrator,
                   PostIntegrator):
        pyblish.api.register_plugin(Plugin)

    pyblish.util.collect()

    assert count["#"] == 1
    count["#"] = 0

    pyblish.util.validate()

    assert count["#"] == 11

    count["#"] = 0
    pyblish.util.extract()

    assert count["#"] == 111

    # Integration runs integration, but also anything after
    count["#"] = 0
    pyblish.util.integrate()

    assert count["#"] == 11111


@with_setup(lib.setup, lib.teardown)
def test_multiple_instance_util_publish():
    """Multiple instances work with util.publish()

    This also ensures it operates correctly with an
    InstancePlugin collector.

    """

    count = {"#": 0}

    class MyContextCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("A")
            context.create_instance("B")
            count["#"] += 1

    class MyInstancePluginCollector(pyblish.api.InstancePlugin):
        order = pyblish.api.CollectorOrder + 0.1

        def process(self, instance):
            count["#"] += 1

    pyblish.api.register_plugin(MyContextCollector)
    pyblish.api.register_plugin(MyInstancePluginCollector)

    # Ensure it runs without errors
    pyblish.util.publish()

    assert count["#"] == 3
