
from . import lib

import pyblish.util
import pyblish.plugin
import pyblish.logic

from pyblish.vendor import mock
from pyblish.vendor.nose.tools import *
from .lib import (
    teardown, FAMILY, HOST, setup_failing, setup_full,
    setup, setup_empty, setup_wildcard)


@mock.patch('pyblish.util.log')
@with_setup(setup_full, teardown)
def test_publish_all(_):
    """publish() calls upon each convenience function"""
    plugins = pyblish.plugin.discover()

    assert "ConformInstances" in [p.__name__ for p in plugins]
    assert "SelectInstances" in [p.__name__ for p in plugins]
    assert "ValidateInstances" in [p.__name__ for p in plugins]
    assert "ExtractInstances" in [p.__name__ for p in plugins]

    context = pyblish.util.publish()
    assert_equals(len(context), 1)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is True


@with_setup(setup_full, teardown)
def test_publish_all_no_context():
    """Not passing a context is fine"""
    context = pyblish.util.publish()
    assert_equals(len(context), 1)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is True
        assert instance.data('conformed') is True


@mock.patch('pyblish.util.log')
@with_setup(setup_full, teardown)
def test_validate_all(_):
    """validate_all() calls upon two of the convenience functions"""
    context = pyblish.plugin.Context()
    pyblish.util.validate_all(context=context)
    assert_equals(len(context), 1)

    for instance in context:
        assert instance.data('selected') is True
        assert instance.data('validated') is True
        assert instance.data('extracted') is False
        assert instance.data('conformed') is False


@mock.patch('pyblish.util.log')
@with_setup(setup_full, teardown)
def test_convenience(_):
    """Convenience function work"""
    context = pyblish.plugin.Context()
    pyblish.util.select(context=context)
    assert_equals(len(context), 1)

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
@with_setup(setup_failing, teardown)
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


@with_setup(setup_empty, teardown)
def test_process():
    """processing works well"""

    _disk = list()

    class SelectInstance(pyblish.plugin.Selector):
        def process_context(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "MyFamily")
            instance.set_data("value", "secret")

    class ValidateInstance(pyblish.plugin.Validator):
        def process_instance(self, instance):
            print "Setting valid to true"
            instance.set_data("valid", True)

    class ExtractInstance(pyblish.plugin.Extractor):
        def process_instance(self, instance):
            assert instance.data("valid") is True
            _disk.append(instance.data("value"))

    for plugin in (SelectInstance, ValidateInstance, ExtractInstance):
        pyblish.plugin.register_plugin(plugin)

    pyblish.util.publish()

    assert _disk[0] == "secret"


@raises(ValueError)
@with_setup(setup_wildcard, teardown)
def test_wildcard_plugins():
    """Wildcard plugins process instances without family"""
    context = pyblish.plugin.Context()

    for type in ('selectors', 'validators'):
        for plugin in pyblish.plugin.discover(type=type):
            for instance, error in pyblish.util.process(plugin, context):
                if error:
                    raise error


@with_setup(setup_empty, teardown)
def test_inmemory_svec():
    """SVEC works fine with in-memory plug-ins"""

    _disk = list()
    _server = dict()

    class SelectInstances(pyblish.plugin.Selector):
        def process_context(self, context):
            instance = context.create_instance(name="MyInstance")
            instance.set_data("family", "MyFamily")

            SomeData = type("SomeData", (object,), {})
            SomeData.value = "MyValue"

            instance.add(SomeData)

    class ValidateInstances(pyblish.plugin.Validator):
        def process_instance(self, instance):
            assert_equals(instance.data("family"), "MyFamily")

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

    assert_equals(_disk[0].value, "MyValue")
    assert_equals(_server["assets"][0].value, "MyValue")
    assert_equals(_server["assets"][0].metadata, "123")


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

    assert_true(value["a"])


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_process_context_error():
    """Processing context raises an exception"""

    context = pyblish.plugin.Context()

    selectors = pyblish.plugin.discover(
        'selectors', regex='^SelectInstancesError$')

    for selector in selectors:
        pyblish.util.process_all(selector, context)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_extraction_failure():
    """Extraction fails ok

    When extraction fails, it is imperitative that other extractors
    keep going and that the user is properly notified of the failure.

    """
    context = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    instance = context.create_instance(name='test_instance')

    instance.add('test_PLY')
    instance.set_data(lib.config['identifier'], value=True)
    instance.set_data('family', value=FAMILY)

    context.add(instance)

    # Assuming validations pass
    extractor = pyblish.plugin.discover(
        type='extractors', regex='.*Fail$')[0]

    print extractor
    assert extractor.__name__ == "ExtractInstancesFail"
    pyblish.util.process_all(extractor, context)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_validation_failure():
    """Validation throws exception upon failure"""

    context = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    instance = context.create_instance(name='test_instance')

    instance.add('test_PLY')
    instance.add('test_misnamed')

    instance.set_data(lib.config['identifier'], value=True)
    instance.set_data('family', value=FAMILY)

    context.add(instance)

    validator = pyblish.plugin.discover(
        type='validators', regex='^ValidateInstanceFail$')[0]

    pyblish.util.process_all(validator, context)


@with_setup(setup, teardown)
def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    context = pyblish.plugin.Context()

    instance = context.create_instance(name='MyInstance')
    instance.add('node1')
    instance.add('node2')
    instance.set_data(lib.config['identifier'], value=True)

    assert len(context) == 1

    for result in pyblish.logic.process(
            plugins=pyblish.plugin.discover(
                'selectors', regex='SelectInstances$'),
            process=pyblish.util.process,
            context=context):
        assert_equals(result.get("error"), None)

    pyblish.util.publish(context)

    # At least one plugin will append a selector
    assert instance in context
    assert len(context) > 1


@with_setup(setup, teardown)
def test_interface():
    """The interface of plugins works fine"""
    context = pyblish.plugin.Context()
    instance = context.create_instance(name='test_instance')
    instance.add('test_PLY')

    for result in pyblish.logic.process(
            plugins=pyblish.plugin.discover(),
            process=pyblish.util.process,
            context=context):
        assert_equals(result.get("error"), None)


def test_failing_context():
    """Context processing yields identical information to instances"""

    class SelectFailure(pyblish.plugin.Selector):
        def process_context(self, context):
            assert False, "I was programmed to fail"

    context = pyblish.plugin.Context()

    for result in pyblish.logic.process(
            plugins=[SelectFailure],
            process=pyblish.util.process,
            context=context):
        error = result.get("error")
        assert_not_equals(error, None)
        assert_true(hasattr(error, "traceback"))
        assert_true(error.traceback is not None)


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

    result = pyblish.util.process(ValidateFailure, context, instance)
    error = result["error"]
    assert_equal(error.message, "instance failed")
    assert_true(hasattr(error, "traceback"))


@with_setup(setup_empty, teardown)
def test_order():
    """Ordering with util.publish works fine"""

    class SelectInstance(pyblish.plugin.Selector):
        def process_context(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("current", "1")

    class Validator1(pyblish.plugin.Validator):
        def process_instance(self, instance):
            value = instance.data("current") + "2"
            instance.set_data("current", value)

    class Validator2(pyblish.plugin.Validator):
        order = pyblish.plugin.Validator.order + 0.1
        def process_instance(self, instance):
            value = instance.data("current") + "3"
            instance.set_data("current", value)

    class Validator3(pyblish.plugin.Validator):
        order = pyblish.plugin.Validator.order + 0.2
        def process_instance(self, instance):
            value = instance.data("current") + "4"
            instance.set_data("current", value)

    class Extractor1(pyblish.plugin.Extractor):
        def process_instance(self, instance):
            value = instance.data("current") + "5"
            instance.set_data("current", value)

    class Extractor2(pyblish.plugin.Extractor):
        order = pyblish.plugin.Extractor.order + 0.1
        def process_instance(self, instance):
            value = instance.data("current") + "6"
            instance.set_data("current", value)

    for plugin in (Extractor2, Extractor1, Validator3,
                   Validator2, Validator1, SelectInstance):
        pyblish.plugin.register_plugin(plugin)

    context = pyblish.util.publish()

    assert_equal(len(context), 1)
    assert_equal(context[0].data("current"), "123456")


def test_plugins_by_family():
    """plugins_by_family works fine"""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    assert_equals(pyblish.logic.plugins_by_family(
                  (Plugin1, Plugin2), family="a"),
                  [Plugin1])


def test_plugins_by_host():
    """plugins_by_host works fine."""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.hosts = ["a"]
    Plugin2.hosts = ["b"]

    assert_equals(pyblish.logic.plugins_by_host(
                  (Plugin1, Plugin2), host="a"),
                  [Plugin1])


def test_plugins_by_instance():
    """plugins_by_instance works fine."""
    Plugin1 = type("Plugin1", (pyblish.plugin.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.plugin.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    instance = pyblish.plugin.Instance("A")
    instance.set_data("family", "a")

    assert_equals(pyblish.logic.plugins_by_instance(
                  (Plugin1, Plugin2), instance),
                  [Plugin1])


@with_setup(setup, teardown)
def test_instances_by_plugin():
    """Returns instances compatible with plugin"""
    ctx = pyblish.plugin.Context()

    # Generate two instances, only one of which will be
    # compatible with the given plugin below.
    families = (FAMILY, 'test.other_family')
    for family in families:
        inst = ctx.create_instance(
            name='TestInstance{0}'.format(families.index(family) + 1))

        inst.set_data(lib.config['identifier'], value=True)
        inst.set_data('family', value=family)
        inst.set_data('host', value='python')

        ctx.add(inst)

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
