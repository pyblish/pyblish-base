
import os
import time
import shutil
import tempfile

from . import lib

import pyblish.util
import pyblish.plugin

from pyblish.vendor import mock
from pyblish.vendor.nose.tools import *
from pyblish.tests.lib import (
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

    ctx = pyblish.util.publish()

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.log')
def test_publish_all_no_instances(mock_log):
    """Having no instances is fine, a warning is logged"""
    ctx = pyblish.plugin.Context()
    pyblish.util.publish(ctx)
    assert mock_log.warning.called


@with_setup(setup_full, teardown)
def test_publish_all_no_context():
    """Not passing a context is fine"""
    ctx = pyblish.util.publish()

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.log')
@with_setup(setup_full, teardown)
def test_validate_all(_):
    """validate_all() calls upon two of the convenience functions"""
    ctx = pyblish.plugin.Context()
    pyblish.util.validate_all(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False


@mock.patch('pyblish.util.log')
@with_setup(setup_full, teardown)
def test_convenience(_):
    """Convenience function work"""
    ctx = pyblish.plugin.Context()

    pyblish.util.select(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is False
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False

    pyblish.util.validate(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is False
        assert inst.data('conformed') is False

    pyblish.util.extract(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is False

    pyblish.util.conform(context=ctx)

    for inst in ctx:
        assert inst.data('selected') is True
        assert inst.data('validated') is True
        assert inst.data('extracted') is True
        assert inst.data('conformed') is True


@mock.patch('pyblish.util.log')
@with_setup(setup_failing, teardown)
def test_main_safe_processes_fail(_):
    """Failing selection, extraction or conform merely logs a message"""
    ctx = pyblish.plugin.Context()
    pyblish.util.select(ctx)

    # Give plugins something to process
    inst = ctx.create_instance(name='TestInstance')
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value=HOST)

    pyblish.util.extract(ctx)
    pyblish.util.conform(ctx)


def test_process():
    """process() works well"""

    _disk = list()

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "MyFamily")
            instance.set_data("value", "secret")

    class ValidateInstance(pyblish.api.Validator):
        def process_instance(self, instance):
            print "Setting valid to true"
            instance.set_data("valid", True)

    class ExtractInstance(pyblish.api.Extractor):
        def process_instance(self, instance):
            assert instance.data("valid") is True
            _disk.append(instance.data("value"))

    context = pyblish.api.Context()
    for plugin in (SelectInstance, ValidateInstance, ExtractInstance):
        for instance, error in pyblish.util.process(plugin, context):
            pass

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

    class SelectInstances(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance(name="MyInstance")
            instance.set_data("family", "MyFamily")

            SomeData = type("SomeData", (object,), {})
            SomeData.value = "MyValue"

            instance.add(SomeData)

    class ValidateInstances(pyblish.api.Validator):
        def process_instance(self, instance):
            assert_equals(instance.data("family"), "MyFamily")

    class ExtractInstances(pyblish.api.Extractor):
        def process_instance(self, instance):
            for child in instance:
                _disk.append(child)

    class IntegrateInstances(pyblish.api.Integrator):
        def process_instance(self, instance):
            _server["assets"] = list()

            for asset in _disk:
                asset.metadata = "123"
                _server["assets"].append(asset)

    for plugin in (SelectInstances,
                   ValidateInstances,
                   ExtractInstances,
                   IntegrateInstances):
        pyblish.api.register_plugin(plugin)

    context = pyblish.api.Context()
    for plugin in pyblish.api.discover():
        for instance, error in pyblish.util.process(plugin, context):
            pass

    assert_equals(_disk[0].value, "MyValue")
    assert_equals(_server["assets"][0].value, "MyValue")
    assert_equals(_server["assets"][0].metadata, "123")


def test_failing_context_processing():
    """Plug-in should not skip processing of Instance if Context fails"""

    value = {"a": False}

    class MyPlugin(pyblish.api.Validator):
        families = ["myFamily"]
        hosts = ["python"]

        def process_context(self, context):
            raise Exception("Failed")

        def process_instance(self, instance):
            value["a"] = True

    ctx = pyblish.api.Context()
    inst = ctx.create_instance(name="MyInstance")
    inst.set_data("family", "myFamily")

    for instance, error in pyblish.util.process(MyPlugin, ctx):
        pass

    assert_true(value["a"])


@with_setup(setup, teardown)
def test_commit():
    """pylish.plugin.commit() works

    Testing commit() involves creating temporary output,
    committing said output and then checking that it
    resides where we expected it to reside.

    """

    ctx = pyblish.plugin.Context()
    inst = ctx.create_instance(name='CommittedInstance')
    inst.set_data('family', FAMILY)

    try:
        # This is where we'll write it first
        temp_dir = tempfile.mkdtemp()
        ctx.set_data('temp_dir', value=temp_dir)

        # This is where the data will eventually end up
        workspace = tempfile.mkdtemp()
        current_file = os.path.join(workspace, 'document_name.txt')
        ctx.set_data('current_file', value=current_file)

        # And this is what we'll write
        document_name = 'document_name'
        document_content = 'document content'
        document = {document_name: document_content}
        inst.add(document)

        date = pyblish.lib.format_filename(pyblish.util.time())
        ctx.set_data("date", date)

        document_extractor = pyblish.plugin.discover(
            'extractors', regex='^ExtractDocuments$')[0]

        for instance, error in pyblish.util.process(document_extractor, ctx):
            assert_equals(error, None)

        for root, dirs, files in os.walk(workspace):
            # The inner-most file is commited document
            document_path = root
            for fn in files:
                document_path = os.path.join(document_path, fn)

        basename = os.path.basename(document_path)
        name, ext = os.path.splitext(basename)

        assert_equals(name, document_name)
        with open(document_path) as f:
            assert f.read() == document_content

        # Data is persisted within each instance
        assert inst.data('commit_dir') == os.path.dirname(document_path)

    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(workspace)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_process_context_error():
    """Processing context raises an exception"""

    ctx = pyblish.plugin.Context()

    selectors = pyblish.plugin.discover(
        'selectors', regex='^SelectInstancesError$')

    for selector in selectors:
        pyblish.util.process_all(selector, ctx)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_extraction_failure():
    """Extraction fails ok

    When extraction fails, it is imperitative that other extractors
    keep going and that the user is properly notified of the failure.

    """
    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.set_data(lib.config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    # Assuming validations pass
    extractor = pyblish.plugin.discover(
        type='extractors', regex='.*Fail$')[0]

    print extractor
    assert extractor.__name__ == "ExtractInstancesFail"
    pyblish.util.process_all(extractor, ctx)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_validation_failure():
    """Validation throws exception upon failure"""

    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.add('test_misnamed')

    inst.set_data(lib.config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    validator = pyblish.plugin.discover(
        type='validators', regex='^ValidateInstanceFail$')[0]

    pyblish.util.process_all(validator, ctx)


@with_setup(setup, teardown)
def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    ctx = pyblish.plugin.Context()

    inst = ctx.create_instance(name='MyInstance')
    inst.add('node1')
    inst.add('node2')
    inst.set_data(lib.config['identifier'], value=True)

    assert len(ctx) == 1

    for selector in pyblish.plugin.discover(
            'selectors', regex='SelectInstances$'):
        pyblish.util.process_all(selector, ctx)

    # At least one plugin will append a selector
    assert inst in ctx
    assert len(ctx) > 1


@with_setup(setup, teardown)
def test_extraction_interface():
    """The interface of extractors works fine"""
    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.set_data(lib.config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    # Assuming validations pass

    extractor = pyblish.plugin.discover(
        type='extractors', regex='.*ExtractInstances$')[0]
    assert extractor.__name__ == "ExtractInstances"

    pyblish.util.process_all(extractor, ctx)


@with_setup(setup, teardown)
def test_selection_interface():
    """The interface of selection works fine"""

    ctx = pyblish.plugin.Context()

    selectors = pyblish.plugin.discover(
        type='selectors',
        regex='SelectInstances$')

    assert len(selectors) >= 1

    for selector in selectors:
        if HOST not in selector.hosts:
            continue

        pyblish.util.process_all(selector, ctx)

    assert len(ctx) >= 1

    inst = ctx.pop()
    assert len(inst) >= 3


@with_setup(setup, teardown)
def test_validation_interface():
    """The interface of validation works fine"""
    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')
    inst.add('test_node1_PLY')
    inst.add('test_node2_PLY')
    inst.add('test_node3_GRP')
    inst.set_data(lib.config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    validator = pyblish.plugin.discover(
        type='validators',
        regex="^ValidateInstance$")[0]

    print "%s found" % validator
    assert validator

    for instance, error in pyblish.util.process(validator, ctx):
        print error
        assert error is None


def test_failing_context():
    """Context processing yields identical information to instances"""

    class SelectFailure(pyblish.api.Selector):
        def process_context(self, context):
            raise pyblish.api.SelectionError("I was programmed to fail")

    ctx = pyblish.api.Context()

    for instance, error in pyblish.util.process(SelectFailure, ctx):
        assert_true(error is not None)
        assert_true(hasattr(error, "traceback"))
        assert_true(error.traceback is not None)


def test_failing_validator():
    """All plug-ins yield both context and instance exceptions"""
    class ValidateFailure(pyblish.api.Validator):
        families = ["test"]

        def process_context(self, context):
            raise pyblish.api.ValidationError("context failed")

        def process_instance(self, instance):
            raise pyblish.api.ValidationError("instance failed")

    ctx = pyblish.api.Context()
    instance = ctx.create_instance("MyInstance")
    instance.set_data("family", "test")

    # Context is always processed first
    processor = pyblish.util.process(ValidateFailure, ctx)
    instance, error = processor.next()
    assert_equal(error.message, "context failed")
    assert_true(hasattr(error, "traceback"))

    # Next up is the instance
    instance, error = processor.next()
    assert_equal(error.message,  "instance failed")
    assert_true(hasattr(error, "traceback"))
    assert_equal(instance.name, "MyInstance")

    # Nothing else is yeilded
    assert_raises(StopIteration, processor.next)


@with_setup(setup_empty, teardown)
def test_order():
    """Ordering with util.publish works fine"""

    class SelectInstance(pyblish.api.Selector):
        def process_context(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("current", "1")

    class Validator1(pyblish.api.Validator):
        def process_instance(self, instance):
            value = instance.data("current") + "2"
            instance.set_data("current", value)

    class Validator2(pyblish.api.Validator):
        order = pyblish.api.Validator.order + 0.1
        def process_instance(self, instance):
            value = instance.data("current") + "3"
            instance.set_data("current", value)

    class Validator3(pyblish.api.Validator):
        order = pyblish.api.Validator.order + 0.2
        def process_instance(self, instance):
            value = instance.data("current") + "4"
            instance.set_data("current", value)

    class Extractor1(pyblish.api.Extractor):
        def process_instance(self, instance):
            value = instance.data("current") + "5"
            instance.set_data("current", value)

    class Extractor2(pyblish.api.Extractor):
        order = pyblish.api.Extractor.order + 0.1
        def process_instance(self, instance):
            value = instance.data("current") + "6"
            instance.set_data("current", value)

    for plugin in (Extractor2, Extractor1, Validator3,
                   Validator2, Validator1, SelectInstance):
        pyblish.api.register_plugin(plugin)

    ctx = pyblish.util.publish()

    assert_equal(len(ctx), 1)
    assert_equal(ctx[0].data("current"), "123456")
