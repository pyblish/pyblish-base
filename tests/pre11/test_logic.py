from unittest import mock

from . import lib

import pyblish.util
import pyblish.plugin
import pyblish.logic

from nose2.tools.decorators import (
    with_setup,
    with_teardown
)
from .lib import (
    teardown, FAMILY, HOST, setup_failing, setup_full,
    setup, setup_empty, setup_wildcard)


@mock.patch('pyblish.util.log')
@with_setup(setup_full)
@with_teardown(teardown)
def test_publish_all(_):
    """publish() calls upon each convenience function"""
    plugins = pyblish.plugin.discover()

    assert "ConformInstances" in [p.__name__ for p in plugins]
    assert "SelectInstances" in [p.__name__ for p in plugins]
    assert "ValidateInstances" in [p.__name__ for p in plugins]
    assert "ExtractInstances" in [p.__name__ for p in plugins]

    context = pyblish.util.publish_all()
    assert len(context) == 1

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is True


@with_setup(setup_full)
@with_teardown(teardown)
def test_publish_all_no_context():
    """Not passing a context is fine"""
    context = pyblish.util.publish_all()
    assert len(context) == 1

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is True


@mock.patch('pyblish.util.log')
@with_setup(setup_full)
@with_teardown(teardown)
def test_validate_all(_):
    """validate_all() calls upon two of the convenience functions"""
    context = pyblish.plugin.Context()
    pyblish.util.validate_all(context=context)
    assert len(context) == 1

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is False
        assert instance.data('conformed') is False


@mock.patch('pyblish.util.log')
@with_setup(setup_full)
@with_teardown(teardown)
def test_convenience(_):
    """Convenience function work"""
    context = pyblish.plugin.Context()
    pyblish.util.select(context=context)
    assert len(context) == 1

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is False
        assert instance.data('extracted') is False
        assert instance.data('conformed') is False

    pyblish.util.validate(context=context)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is False
        assert instance.data('conformed') is False

    pyblish.util.extract(context=context)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is False

    pyblish.util.conform(context=context)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is True


@mock.patch('pyblish.util.log')
@with_setup(setup_failing)
@with_teardown(teardown)
def test_main_safe_processes_fail(_):
    """Failing selection, extraction or conform merely logs a message"""
    context = pyblish.plugin.Context()
    pyblish.util.select(context)

    # Give plugins something to process
    instance = context.create_instance(name='TestInstance')
    instance.set_data('family', value=FAMILY)
    instance.set_data('host', value=HOST)

    pyblish.util.extract(context)
    pyblish.util.conform(context)


@with_setup(setup_empty)
@with_teardown(teardown)
def test_process():
    """processing works well"""

    _disk = list()

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "MyFamily")
            instance.set_data("value", "secret")

    class ValidateInstance(pyblish.plugin.Validator):
        def process_instance(self, instance):
            self.log.critical("Setting valid to true")
            instance.set_data("valid", True)

    class ExtractInstance(pyblish.plugin.Extractor):
        def process_instance(self, instance):
            assert instance.data("valid") is True
            _disk.append(instance.data("value"))

    for plugin in (SelectInstance, ValidateInstance, ExtractInstance):
        pyblish.plugin.register_plugin(plugin)

    pyblish.util.publish()

    assert _disk[0] == "secret"


@with_setup(setup_wildcard)
@with_teardown(teardown)
def test_wildcard_plugins():
    """Wildcard plugins process instances without family"""
    context = pyblish.plugin.Context()

    plugin = pyblish.plugin.discover(type="selectors")[0]
    iterator = pyblish.logic.process(
        func=pyblish.plugin.process,
        plugins=[plugin],
        context=context)

    result = next(iterator)
    assert result["plugin"] == plugin
    assert next(iterator, None) == None

    plugin = [p for p in pyblish.plugin.discover()
              if issubclass(p, pyblish.api.Validator)][0]

    iterator = pyblish.logic.process(
        func=pyblish.plugin.process,
        plugins=[plugin],
        context=context)

    result = next(iterator)
    assert isinstance(result["error"], Exception)


@with_setup(setup_empty)
@with_teardown(teardown)
def test_inmemory_svec():
    """SVEC works fine with in-memory plug-ins"""

    _disk = list()
    _server = dict()

    class SelectInstances(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance(name="MyInstance")
            instance.set_data("family", "MyFamily")

            SomeData = type("SomeData", (object,), {})
            SomeData.value = "MyValue"

            instance.add(SomeData)

    class ValidateInstances(pyblish.plugin.Validator):
        def process_instance(self, instance):
            assert instance.data("family") == "MyFamily"

    class ExtractInstances(pyblish.plugin.Extractor):
        def process_instance(self, instance):
            for child in instance:
                _disk.append(child)

    class IntegrateInstances(pyblish.plugin.Integrator):
        def process_instance(self, instance):
            _server["assets"] = list()

            for asset in _disk:
                asset.metadata = "123"
                _server["assets"].append(asset)

    for plugin in (SelectInstances,
                   ValidateInstances,
                   ExtractInstances,
                   IntegrateInstances):
        pyblish.plugin.register_plugin(plugin)

    pyblish.util.publish()

    assert _disk[0].value == "MyValue"
    assert _server["assets"][0].value == "MyValue"
    assert _server["assets"][0].metadata == "123"


def test_failing_context_processing():
    """Plug-in should not skip processing of Instance if Context fails"""

    value = {"a": False}

    class MyPlugin(pyblish.plugin.Validator):
        families = ["myFamily"]
        hosts = ["python"]

        def process_context(self, context):
            raise Exception("Failed")

        def process_instance(self, instance):
            value["a"] = True

    context = pyblish.plugin.Context()
    instance = context.create_instance(name="MyInstance")
    instance.set_data("family", "myFamily")

    pyblish.plugin.register_plugin(MyPlugin)
    pyblish.util.publish(context=context)

    assert value["a"]


@with_setup(setup_failing)
@with_teardown(teardown)
def test_process_context_error():
    """Processing context raises an exception"""

    context = pyblish.plugin.Context()
    
    @pyblish.api.log
    class SelectInstancesError(pyblish.api.Selector):
        hosts = ['python']
        version = (0, 1, 0)
    
        def process_context(self, context):
            raise ValueError("Test exception")

    iterator = pyblish.logic.process(
        func=pyblish.plugin.process,
        plugins=[SelectInstancesError],
        context=context)

    result = next(iterator)
    assert result["plugin"] == SelectInstancesError
    assert isinstance(result["error"], Exception)


@with_setup(setup_failing)
@with_teardown(teardown)
def test_extraction_failure():
    """Extraction fails ok

    When extraction fails, it is imperitative that other extractors
    keep going and that the user is properly notified of the failure.

    """
    context = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    instance = context.create_instance(name='test_instance')

    instance.add('test_PLY')
    instance.set_data("publishable", value=True)
    instance.set_data('family', value=FAMILY)

    # Assuming validations pass
    plugins = dict((p.__name__, p) for p in pyblish.plugin.discover())
    extractor = plugins["ExtractInstancesFail"]

    print(extractor)
    assert extractor.__name__ == "ExtractInstancesFail"
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[extractor],
            context=context):

        if result["error"] is not None:
            assert isinstance(result["error"], Exception)


@with_setup(setup)
@with_teardown(teardown)
def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    context = pyblish.plugin.Context()

    instance = context.create_instance(name='MyInstance')
    instance.add('node1')
    instance.add('node2')
    instance.set_data("publishable", value=True)

    assert len(context) == 1

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=pyblish.plugin.discover(
                'selectors', regex='SelectInstances$'),
            context=context):
        assert result.get("error") == None

    pyblish.util.publish(context)

    # At least one plugin will append a selector
    assert instance in context
    assert len(context) > 1


@with_setup(setup_empty)
@with_teardown(teardown)
def test_interface():
    """The interface of plugins works fine"""
    context = pyblish.plugin.Context()

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance(name='test_instance')
            instance.add('test_PLY')

    class ValidateInstance(pyblish.api.Validator):
        def process_instance(self, instance):
            assert True

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectInstance, ValidateInstance],
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            print(result)

        if isinstance(result, Exception):
            raise result

        assert result.get("error") == None


def test_failing_context():
    """Context processing yields identical information to instances"""

    class SelectFailure(pyblish.api.Selector):
        def process_context(self, context):
            assert False, "I was programmed to fail"

    context = pyblish.plugin.Context()

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectFailure],
            context=context):
        error = result.get("error")
        assert error is not None
        assert hasattr(error, "traceback")
        assert error.traceback is not None


def test_failing_validator():
    """When both context and instance fails, only return instance error

    This is because there is no way of including both errors, and any
    error is enough cause for a plug-in to fail. This is solved
    in 1.1 via DI.

    """

    class ValidateFailure(pyblish.plugin.Validator):
        families = ["test"]

        def process_context(self, context):
            assert False, "context failed"

        def process_instance(self, instance):
            assert False, "instance failed"

    context = pyblish.plugin.Context()
    instance = context.create_instance("MyInstance")
    instance.set_data("family", "test")

    iterator = pyblish.logic.process(
        func=pyblish.plugin.process,
        plugins=[ValidateFailure],
        context=context)
    result = next(iterator)
    error = result["error"]
    assert str(error) == "instance failed"
    assert hasattr(error, "traceback")


@with_setup(setup_empty)
@with_teardown(teardown)
def test_order():
    """Ordering with util.publish works fine"""

    order = {"#": "0"}

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            order["#"] += "1"
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")

    class Validator1(pyblish.plugin.Validator):
        def process_instance(self, instance):
            order["#"] += "2"

    class Validator2(pyblish.plugin.Validator):
        order = pyblish.plugin.Validator.order + 0.1

        def process_instance(self, instance):
            order["#"] += "3"

    class Validator3(pyblish.plugin.Validator):
        order = pyblish.plugin.Validator.order + 0.2

        def process_instance(self, instance):
            order["#"] += "4"

    class Extractor1(pyblish.plugin.Extractor):
        def process_instance(self, instance):
            order["#"] += "5"

    class Extractor2(pyblish.plugin.Extractor):
        order = pyblish.plugin.Extractor.order + 0.1

        def process_instance(self, instance):
            order["#"] += "6"

    for plugin in (Extractor2, Extractor1, Validator3,
                   Validator2, Validator1, SelectInstance):
        pyblish.plugin.register_plugin(plugin)

    pyblish.util.publish()
    assert order["#"] == "0123456"


def test_plugins_by_family():
    """plugins_by_family works fine"""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    assert (pyblish.logic.plugins_by_family(
                  (Plugin1, Plugin2), family="a") ==
                  [Plugin1])


def test_plugins_by_host():
    """plugins_by_host works fine."""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.hosts = ["a"]
    Plugin2.hosts = ["b"]

    assert (pyblish.logic.plugins_by_host(
                  (Plugin1, Plugin2), host="a") == 
                  [Plugin1])


def test_plugins_by_instance():
    """plugins_by_instance works fine."""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    instance = pyblish.plugin.Instance("A")
    instance.set_data("family", "a")

    assert (pyblish.logic.plugins_by_instance(
                  (Plugin1, Plugin2), instance) ==
                  [Plugin1])


@with_setup(setup)
@with_teardown(teardown)
def test_instances_by_plugin():
    """Returns instances compatible with plugin"""
    ctx = pyblish.plugin.Context()

    # Generate two instances, only one of which will be
    # compatible with the given plugin below.
    families = (FAMILY, 'test.other_family')
    for family in families:
        inst = ctx.create_instance(
            name='TestInstance{0}'.format(families.index(family) + 1))

        inst.set_data("publishable", value=True)
        inst.set_data('family', value=family)
        inst.set_data('host', value='python')

    plugins = pyblish.plugin.discover('validators')
    plugins_dict = dict()

    for plugin in plugins:
        plugins_dict[plugin.__name__] = plugin

    plugin = plugins_dict['ValidateInstance']

    compatible = pyblish.logic.instances_by_plugin(
        instances=ctx, plugin=plugin)

    # This plugin is only compatible with
    # the family is "TestInstance1"
    assert compatible[0].name == 'TestInstance1'


@with_setup(setup_empty)
@with_teardown(teardown)
def test_repair():
    """Repairing works well"""

    _data = {}

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            context.create_instance("MyInstance")

    class ValidateInstance(pyblish.api.Validator):
        def process_instance(self, instance):
            _data["broken"] = True
            assert False, "Broken"

        def repair_instance(self, instance):
            _data["broken"] = False

    context = pyblish.api.Context()

    results = list()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectInstance, ValidateInstance],
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            assert str(result) == "Broken"

        results.append(result)

    assert _data["broken"]

    repair = list()
    for result in results:
        if result["error"]:
            repair.append(result["plugin"])

    for result in pyblish.logic.process(
            func=pyblish.plugin.repair,
            plugins=repair,
            context=context):
        print(result)

    assert not _data["broken"]


@with_setup(lib.setup_empty)
@with_teardown(lib.teardown)
def test_context_once():
    """Context is only processed once"""

    count = {"#": 0}

    class SelectMany(pyblish.api.Selector):
        def process_context(self, context):
            for name in ("A", "B", "C"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

    class ValidateContext(pyblish.api.Validator):
        def process_context(self, context):
            count["#"] += 1

    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectMany, ValidateContext],
            context=context):
        pass

    assert count["#"] == 1


@with_setup(lib.setup_empty)
@with_teardown(lib.teardown)
def test_instance_every():
    """Plug-ins process each instance"""

    count = {"#": 0}

    class SelectMany(pyblish.api.Selector):
        def process_context(self, context):
            for name in ("A", "B", "C"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

    class ValidateContext(pyblish.api.Validator):
        def process_instance(self, instance):
            count["#"] += 1

    context = pyblish.api.Context()
    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=[SelectMany, ValidateContext],
            context=context):
        pass

    assert count["#"] == 3
