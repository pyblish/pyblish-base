from . import lib

import pyblish.lib
import pyblish.compat
from nose.tools import (
    with_setup
)


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
    context = pyblish.util.publish()

    assert count["#"] == 3
