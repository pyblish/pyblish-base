
# Local library
from .. import lib
from pyblish import api, _logic, _plugin
from nose.tools import (
    with_setup,
    assert_equals,
    assert_raises,
    assert_true,
    assert_false
)


@with_setup(lib.setup_empty, lib.teardown)
def test_di():
    """Dependency injection works fine"""

    _disk = dict()

    # Plugins
    class SelectInstance(api.Selector):
        def process(self, context):
            self.log.info("Test")
            for name in ("MyInstanceA", "MyInstanceB"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")
                instance.set_data("value", "123")

            print("Instance: %s" % instance)

    class ValidateInstance(api.Validator):
        def process(self, instance):
            assert instance.data("family") == "myFamily", "Wrong family"

    class ExtractInstanceX(api.Extractor):
        def process(self, context, instance, user, time):
            self.log.warning("Filling up disk..")
            _disk[instance.name] = "%s - %s: %s" % (
                time(), user, instance.data("value"))

    for plugin in (SelectInstance, ValidateInstance, ExtractInstanceX):
        api.register_plugin(plugin)

    context = api.Context()

    for result in _logic.process(
            func=_plugin.process,
            plugins=api.discover(),
            context=context):
        assert result["error"] is None, result["error"]

    assert "MyInstanceB" in _disk


@with_setup(lib.setup_empty, lib.teardown)
def test_init():
    """__init__ is triggered once per process"""

    count = {"#": 0}

    class HappensOnce(api.Selector):
        def __init__(self):
            count["#"] += 1

        def process(self, context):
            for name in ("Smurfette", "Passive-aggressive smurf"):
                instance = context.create_instance(name)
                instance.set_data("family", "smurfFamily")

    class HappensTwice(api.Validator):
        def __init__(self):
            count["#"] += 10

        def process(self, instance):
            pass

    for plugin in (HappensOnce,
                   HappensTwice):
        api.register_plugin(plugin)

    list(_logic.process(
        func=_plugin.process,
        plugins=api.discover(),
        context=api.Context()))

    assert_equals(count["#"], 21)


@with_setup(lib.setup_empty, lib.teardown)
def test_occurence():
    """Test when and how often plug-ins process"""

    count = {"#": 0}

    class HappensOnce1(api.Selector):
        def process(self, context):
            count["#"] += 1
            for name in ("Smurfette", "Passive-aggressive smurf"):
                instance = context.create_instance(name)
                instance.set_data("family", "smurfFamily")

    class HappensOnce2(api.Validator):
        def process(self):
            count["#"] += 1

    class DoesNotHappen1(api.Validator):
        """Doesn't run

        It's requesting to be triggered only in the presence
        of an instance of a family that isn't present.

        """

        families = ["unsupportedFamily"]

        def process(self):
            self.log.critical(str(self))
            count["#"] += 1

    class DoesNotHappen2(api.Validator):
        """Doesn't run.

        Asking for `instance`, and only supporting an unavailable
        family prevents this plug-in from running

        """

        families = ["unsupportedFamily"]

        def process(self, instance):
            self.log.critical(str(self))
            count["#"] += 1

    class HappensEveryInstance(api.Validator):
        def process(self, instance):
            count["#"] += 1

    for plugin in (HappensOnce1,
                   HappensOnce2,
                   DoesNotHappen1,
                   DoesNotHappen2,
                   HappensEveryInstance):
        api.register_plugin(plugin)

    context = api.Context()

    list(_logic.process(
        func=_plugin.process,
        plugins=api.discover(),
        context=context))

    assert_equals(count["#"], 4)


@with_setup(lib.setup_empty, lib.teardown)
def test_no_instances():
    """Run .process at least once per plug-in"""

    count = {"#": 0}

    class Extract(api.Extractor):
        def process(self, context):
            count["#"] += 1

    class Extract2(api.Extractor):
        """This doesn't run

        Because it asks for instance, and there aren't any instances

        """

        def process(self, context, instance):
            assert instance is None
            count["#"] += 1

    class Conform(api.Conformer):
        def process(self, context):
            count["#"] += 1

    for plugin in (Extract, Extract2, Conform):
        api.register_plugin(plugin)

    context = api.Context()

    for result in _logic.process(
            func=_plugin.process,
            plugins=api.discover(),
            context=context):
        pass

    assert_equals(count["#"], 2)


def test_unavailable_service():
    """Asking for unavailable service throws exception"""

    provider = _plugin.Provider()

    def func(arg1, arg2):
        return True

    provider.inject("arg1", lambda: True)
    assert_raises(KeyError, provider.invoke, func)


def test_unavailable_service_logic():
    """Asking for unavailable service ..?"""

    class SelectUnavailable(api.Selector):
        def process(self, unavailable):
            print("HHOH")
            self.log.critical("Test")

    for result in _logic.process(
            func=_plugin.process,
            plugins=[SelectUnavailable],
            context=api.Context()):
        assert_true(isinstance(result["error"], KeyError))


@with_setup(lib.setup_empty, lib.teardown)
def test_test_failure():
    """Failing the test yields an exception"""

    triggered = list()

    class ValidateFailure(api.Validator):
        def process(self, context):
            triggered.append(self)
            assert False

    class ExtractFailure(api.Extractor):
        def process(self, context):
            triggered.append(self)
            pass

    api.register_plugin(ValidateFailure)
    api.register_plugin(ExtractFailure)

    context = api.Context()

    results = list(_logic.process(
        func=_plugin.process,
        plugins=api.discover(),
        context=context))

    assert_equals(len(triggered), 1)
    assert_equals(type(triggered[0]).id, ValidateFailure.id)
    assert_true(isinstance(results[-1], Exception))


@with_setup(lib.setup_empty, lib.teardown)
def test_when_to_trigger_process():
    """process() should be triggered whenever `context` is requested"""

    _data = {"error": False}

    class SelectInstance(api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "compatibleFamily")

    class IncompatibleValidator(api.Validator):
        families = ["incompatibleFamily"]

        def process(self, instance):
            print("Instance is: %s" % instance)
            _data["error"] = True
            assert False, "I should not have been run"

    class CompatibleValiator(api.Validator):
        families = ["compatibleFamily"]

        def process(self, instance):
            assert True

    for plugin in (SelectInstance, IncompatibleValidator, CompatibleValiator):
        api.register_plugin(plugin)

    context = api.Context()
    list(_logic.process(
        func=_plugin.process,
        plugins=api.discover(),
        context=context))

    assert_equals(_data["error"], False)


def test_default_services():
    """Default services are operational"""

    services = ["user", "time"]
    for service in services:
        assert_true(service in api.registered_services())

    # user is passed by value, as it does not change at run-time
    user = api.registered_services()["user"]
    assert_false(hasattr(user, "__call__"))

    # time is passed by reference, and is callable, as it changes
    time = api.registered_services()["time"]
    time()


def test_asset():
    """Assets with DI works well"""

    count = {"#": 0}

    class SelectCharacters(api.Selector):
        """Called once"""
        def process(self, context):
            for name in ("A", "B"):
                context.create_asset(name, family="myFamily")
            count["#"] += 1

    class ValidateColor(api.Validator):
        """Called twice"""
        families = ["myFamily"]

        def process(self, asset):
            count["#"] += 1

    for result in _logic.process(
            func=_plugin.process,
            plugins=[SelectCharacters, ValidateColor],
            context=api.Context()):
        print(result)

    assert_equals(count["#"], 3)


@with_setup(lib.setup_empty, lib.teardown)
def test_di_testing():
    """DI simplifies testing"""

    instances = list()

    class SelectCharacters(api.Validator):
        def process(self, context, host):
            for char in host.ls("*_char"):
                instance = context.create_instance(char, family="character")
                instance.add(host.listRelatives(char))
                instances.append(instance.name)

    class HostMock(object):
        def ls(self, query):
            return ["bobby_char", "rocket_char"]

        def listRelatives(self, node):
            if node == "bobby_char":
                return ["arm", "leg"]
            if node == "rocket_char":
                return ["propeller"]
            return []

    api.register_service("host", HostMock())

    for result in _logic.process(
            func=_plugin.process,
            plugins=[SelectCharacters],
            context=api.Context()):
        assert_equals(result["error"], None)

    assert_equals(len(instances), 2)
    assert_equals(instances, ["bobby_char", "rocket_char"])
