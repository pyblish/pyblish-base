
# Local library
from . import lib
import pyblish.plugin
import pyblish.logic
from pyblish.vendor.nose.tools import *


@with_setup(lib.setup_empty, lib.teardown)
def test_di():
    """Dependency injection works fine"""

    _disk = dict()

    # Plugins
    class SelectInstance(pyblish.api.Selector):
        def process(self, context, instance):
            self.log.info("Test")
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

    for result in pyblish.logic.process(
            plugins=pyblish.api.discover(),
            process=pyblish.util.process,
            context=context):
        print result

    assert "MyInstanceB" in _disk


@with_setup(lib.setup_empty, lib.teardown)
def test_initialisation_only():
    """Not processing, only initialising, still triggers DI"""

    counter = {
        "SelectSmurf": 0,
        "ValidateSmurf": 0
    }

    class SelectSmurf(pyblish.api.Selector):
        def __init__(self):
            counter["SelectSmurf"] += 1

    class ValidateSmurf(pyblish.api.Validator):
        def __init__(self):
            counter["ValidateSmurf"] += 1

    for plugin in (SelectSmurf, ValidateSmurf):
        pyblish.api.register_plugin(plugin)

    context = pyblish.api.Context()

    for result in pyblish.logic.process(
            plugins=pyblish.api.discover(),
            process=pyblish.util.process,
            context=context):
        pass

    assert_equals(counter["SelectSmurf"], 1)
    assert_equals(counter["ValidateSmurf"], 1)


@with_setup(lib.setup_empty, lib.teardown)
def test_no_instances():
    """Run .process at least once per plug-in"""

    count = {"#": 0}

    class Extract(pyblish.api.Extractor):
        def process(self):
            count["#"] += 1

    class Extract2(pyblish.api.Extractor):
        def process(self, context, instance):
            assert instance is None
            count["#"] += 1

    class Conform(pyblish.api.Conformer):
        def process(self):
            count["#"] += 1

    for plugin in (Extract, Extract2, Conform):
        pyblish.api.register_plugin(plugin)

    context = pyblish.api.Context()

    for result in pyblish.logic.process(
            plugins=pyblish.api.discover(),
            process=pyblish.util.process,
            context=context):
        pass

    assert_equals(count["#"], 3)


@with_setup(lib.setup_empty, lib.teardown)
def test_unavailable_service():
    """Asking for unavailable service throws exception"""

    provider = pyblish.plugin.Provider()

    def func(arg1, arg2):
        return True

    provider.inject("arg1", lambda: True)
    assert_raises(KeyError, provider.invoke, func)
