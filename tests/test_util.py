from . import lib

import pyblish.lib
import pyblish.compat
from nose.tools import (
    with_setup
)


@with_setup(lib.setup, lib.teardown)
def test_multiple_instance_publish_util():
    """Multiple instances work with util.publish()

    This also ensures it operates correctly with an
    InstancePlugin collector.

    """

    class MyContextCollector(pyblish.api.ContextPlugin):
    	order = pyblish.api.CollectorOrder
        def process(self, context):
            context.create_instance("A")
            context.create_instance("B")

    class MyInstancePluginCollector(pyblish.api.InstancePlugin):
    	order = pyblish.api.CollectorOrder + 0.1
        def process(self, instance):
            pass

    pyblish.api.register_plugin(MyContextCollector)
    pyblish.api.register_plugin(MyInstancePluginCollector)

    # Ensure it runs without errors
    context = pyblish.util.publish()

