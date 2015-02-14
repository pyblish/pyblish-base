
# Standard library
import os
import time
import shutil
import tempfile

# Local library
import pyblish.plugin

from pyblish.vendor import mock
from pyblish.vendor import yaml

from pyblish.tests.lib import (
    setup, teardown, setup_failing, HOST, FAMILY,
    setup_duplicate, setup_invalid, setup_wildcard)
from pyblish.vendor.nose.tools import raises, with_setup, assert_raises


config = pyblish.plugin.Config()


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

        selector().process_all(ctx)

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
    inst.set_data(config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    validator = pyblish.plugin.discover(
        type='validators',
        regex="^ValidateInstance$")[0]

    print "%s found" % validator
    assert validator

    for instance, error in validator().process(ctx):
        print error
        assert error is None


@with_setup(setup, teardown)
def test_extraction_interface():
    """The interface of extractors works fine"""
    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.set_data(config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    # Assuming validations pass

    extractor = pyblish.plugin.discover(
        type='extractors', regex='.*ExtractInstances$')[0]
    assert extractor.__name__ == "ExtractInstances"

    extractor().process_all(ctx)


@with_setup(setup, teardown)
def test_plugin_interface():
    """All plugins share interface"""

    ctx = pyblish.plugin.Context()

    for plugin in pyblish.plugin.discover():
        for instance, error in plugin().process(ctx):
            assert (error is None) or isinstance(error, Exception)


@with_setup(setup, teardown)
def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    ctx = pyblish.plugin.Context()

    inst = ctx.create_instance(name='MyInstance')
    inst.add('node1')
    inst.add('node2')
    inst.set_data(config['identifier'], value=True)

    assert len(ctx) == 1

    for selector in pyblish.plugin.discover(
            'selectors', regex='SelectInstances$'):
        selector().process_all(context=ctx)

    # At least one plugin will append a selector
    assert inst in ctx
    assert len(ctx) > 1


@with_setup(setup, teardown)
def test_plugins_by_family():
    """Returns plugins compatible with family"""
    inst = pyblish.plugin.Instance('TestInstance')
    inst.set_data(config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    plugins = pyblish.plugin.discover('validators')
    compatible = pyblish.plugin.plugins_by_family(
        plugins, family=FAMILY)

    # The filter will discard at least one plugin
    assert len(plugins) > len(compatible)


@with_setup(setup, teardown)
def test_plugins_by_host():
    """Returns plugins compatible with host"""
    inst = pyblish.plugin.Instance('TestInstance')
    inst.set_data(config['identifier'], value=True)

    plugins = pyblish.plugin.discover('validators')
    compatible = pyblish.plugin.plugins_by_host(
        plugins, host='__unrecognised__')

    # The filter will discard at least one plugin
    print compatible
    assert len(compatible) == 0


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

        inst.set_data(config['identifier'], value=True)
        inst.set_data('family', value=family)
        inst.set_data('host', value='python')

        ctx.add(inst)

    plugins = pyblish.plugin.discover('validators')
    plugins_dict = dict()

    for plugin in plugins:
        plugins_dict[plugin.__name__] = plugin

    plugin = plugins_dict['ValidateInstance']

    compatible = pyblish.plugin.instances_by_plugin(
        instances=ctx, plugin=plugin)

    # This plugin is only compatible with
    # the family is "TestInstance1"
    assert compatible[0].name == 'TestInstance1'


@with_setup(setup, teardown)
def test_print_plugin():
    """Printing plugin returns name of class"""
    plugins = pyblish.plugin.discover('validators')
    plugin = plugins[0]
    assert plugin.__name__ in repr(plugin())
    assert plugin.__name__ == str(plugin())


@with_setup(setup, teardown)
def test_name_override():
    """Instances return either a data-member of name or its native name"""
    inst = pyblish.plugin.Instance(name='my_name')
    assert inst.data('name') == 'my_name'

    inst.set_data('name', value='overridden_name')
    assert inst.data('name') == 'overridden_name'


@with_setup(setup_duplicate, teardown)
def test_no_duplicate_plugins():
    """Discovering plugins results in a single occurence of each plugin"""
    plugin_paths = pyblish.plugin.plugin_paths()
    assert len(plugin_paths) == 2, plugin_paths

    plugins = pyblish.plugin.discover(type='selectors')

    # There are two plugins available, but one of them is
    # hidden under the duplicate module name. As a result,
    # only one of them is returned. A log message is printed
    # to alert the user.
    assert len(plugins) == 1, plugins


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_validation_failure():
    """Validation throws exception upon failure"""

    ctx = pyblish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.add('test_misnamed')

    inst.set_data(config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    validator = pyblish.plugin.discover(
        type='validators', regex='^ValidateInstanceFail$')[0]

    validator().process_all(ctx)


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
    inst.set_data(config['identifier'], value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    # Assuming validations pass
    extractor = pyblish.plugin.discover(
        type='extractors', regex='.*Fail$')[0]

    print extractor
    assert extractor.__name__ == "ExtractInstancesFail"
    extractor().process_all(ctx)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_process_context_error():
    """Processing context raises an exception"""

    ctx = pyblish.plugin.Context()

    selectors = pyblish.plugin.discover(
        'selectors', regex='^SelectInstancesError$')

    for selector in selectors:
        selector().process_all(context=ctx)


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
    inst.set_data(config['identifier'], True)

    try:
        # This is where we'll write it first
        temp_dir = tempfile.mkdtemp()
        ctx.set_data('temp_dir', value=temp_dir)

        # This is where the data will eventually end up
        workspace = tempfile.mkdtemp()
        current_file = os.path.join(workspace, 'document_name.txt')
        ctx.set_data('current_file', value=current_file)

        # Finally, we need a date
        date = time.strftime(config['date_format'])
        ctx.set_data('date', value=date)

        # And this is what we'll write
        document_name = 'document_name'
        document_content = 'document content'
        document = {document_name: document_content}
        inst.add(document)

        document_extractor = pyblish.plugin.discover(
            'extractors', regex='^ExtractDocuments$')[0]

        document_extractor().process_all(ctx)

        for root, dirs, files in os.walk(workspace):
            # The inner-most file is commited document
            document_path = root
            for fn in files:
                document_path = os.path.join(document_path, fn)

        basename = os.path.basename(document_path)
        name, ext = os.path.splitext(basename)

        assert name == document_name
        with open(document_path) as f:
            assert f.read() == document_content

        # Data is persisted within each instance
        assert inst.data('commit_dir') == os.path.dirname(document_path)

    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(workspace)


@with_setup(setup_invalid, teardown)
@mock.patch('pyblish.plugin.log')
def test_invalid_plugins(mock_log):
    """When an invalid plugin is found, an error is logged"""
    pyblish.plugin.discover('selectors')
    assert mock_log.error.called


def test_entities_prints_nicely():
    """Entities Context and Instance prints nicely"""
    ctx = pyblish.plugin.Context()
    inst = ctx.create_instance(name='Test')
    assert 'Instance' in repr(inst)
    assert 'pyblish.plugin' in repr(inst)


def test_deregister_path():
    path = os.path.expanduser('~')
    pyblish.plugin.register_plugin_path(path)
    assert path in pyblish.plugin.registered_paths()
    pyblish.plugin.deregister_plugin_path(path)
    assert path not in pyblish.plugin.registered_paths()


def test_environment_paths():
    """Registering via the environment works"""
    key = config['paths_environment_variable']
    path = '/test/path'
    existing = os.environ.get(key)

    try:
        os.environ[key] = path
        processed = pyblish.plugin._post_process_path(path)
        assert processed in pyblish.plugin.plugin_paths()
    finally:
        os.environ[key] = existing or ''


@raises(ValueError)
def test_discover_invalid_type():
    """Discovering an invalid type raises an error"""
    pyblish.plugin.discover(type='INVALID')


@raises(ValueError)
@with_setup(setup_wildcard, teardown)
def test_wildcard_plugins():
    """Wildcard plugins process instances without family"""
    context = pyblish.plugin.Context()

    for type in ('selectors', 'validators'):
        for plugin in pyblish.plugin.discover(type=type):
            plugin().process_all(context)


def test_instances_by_plugin_invariant():
    ctx = pyblish.plugin.Context()
    for i in range(10):
        inst = ctx.create_instance(name="Instance%i" % i)
        inst.set_data("family", "A")

        if i % 2:
            # Every other instance is of another family
            inst.set_data("family", "B")

    plugin = type("MyPlugin%d" % i, (pyblish.plugin.Validator,), {})
    plugin.hosts = ["python"]
    plugin.families = ["A"]

    compatible = pyblish.plugin.instances_by_plugin(ctx, plugin)

    # Test invariant
    #
    # in:  [1, 2, 3, 4]
    # out: [1, 4] --> good
    #
    # in:  [1, 2, 3, 4]
    # out: [2, 1, 4] --> bad
    #

    def test():
        for instance in compatible:
            assert ctx.index(instance) >= compatible.index(instance)

    test()

    compatible.reverse()
    assert_raises(AssertionError, test)
