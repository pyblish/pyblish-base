
# Local library
from . import lib
import pyblish.plugin
from pyblish.vendor.nose.tools import *


@with_setup(lib.setup_empty, lib.teardown)
def test_di():
    """Dependency injection works fine"""

    _disk = dict()

    # Plugins
    class SelectInstance(pyblish.api.Selector):
        def process(self, context, instance):
            for name in ("MyInstanceA", "MyInstanceB"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")
                instance.set_data("value", "123")

            print "Instance: %s" % instance

    class ValidateInstance(pyblish.api.Validator):
        def process(self, instance):
            assert instance.data("family") == "myFamily", "Wrong family"

    class ExtractInstance(pyblish.api.Extractor):
        def __init__(self):
            super(ExtractInstance, self).__init__()
            self.instance_count = 0

        def process(self, context, instance, user, time):
            self.instance_count += 1

            _disk[instance.name] = "%s - %s: %s (%s)" % (
                time(), user(), instance.data("value"), self.instance_count)

    for plugin in (SelectInstance, ValidateInstance, ExtractInstance):
        pyblish.api.register_plugin(plugin)

    context = pyblish.api.Context()

    for Plugin in pyblish.api.discover():
        for instance, err in pyblish.util.process(Plugin, context):
            print instance, err

    assert "MyInstanceB" in _disk
