
# Standard library
import os
import shutil
import tempfile

# Local library
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin

from pyblish.backend.tests.lib import (
    setup, teardown, setup_failing, HOST, FAMILY,
    setup_duplicate)
from pyblish.vendor.nose.tools import raises, with_setup


@with_setup(setup, teardown)
def test_selection_interface():
    """The interface of selection works fine"""

    ctx = pyblish.backend.plugin.Context()

    selectors = pyblish.backend.plugin.discover(
        type='selectors',
        regex='SelectInstances$')

    assert len(selectors) >= 1

    for selector in selectors:
        if not HOST in selector.hosts:
            continue

        selector().process_all(ctx)

    assert len(ctx) >= 1

    inst = ctx.pop()
    assert len(inst) >= 3


@with_setup(setup, teardown)
def test_validation_interface():
    """The interface of validation works fine"""
    ctx = pyblish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')
    inst.add('test_node1_PLY')
    inst.add('test_node2_PLY')
    inst.add('test_node3_GRP')
    inst.set_data(pyblish.backend.config.identifier, value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    validator = pyblish.backend.plugin.discover(
        type='validators',
        regex="^ValidateInstance$")[0]

    for instance, error in validator().process(ctx):
        assert error is None


@with_setup(setup, teardown)
def test_extraction_interface():
    """The interface of extractors works fine"""
    ctx = pyblish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = ctx.create_instance(name='test_instance')

    inst.add('test_PLY')
    inst.set_data(pyblish.backend.config.identifier, value=True)
    inst.set_data('family', value=FAMILY)

    ctx.add(inst)

    # Assuming validations pass

    extractor = pyblish.backend.plugin.discover(
        type='extractors', regex='.*ExtractInstances$')[0]
    assert extractor.__name__ == "ExtractInstances"

    extractor().process_all(ctx)


@with_setup(setup, teardown)
def test_plugin_interface():
    """All plugins share interface"""

    ctx = pyblish.backend.plugin.Context()

    for plugin in pyblish.backend.plugin.discover():
        for instance, error in plugin().process(ctx):
            assert (error is None) or isinstance(error, Exception)


@with_setup(setup, teardown)
def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    ctx = pyblish.backend.plugin.Context()

    inst = ctx.create_instance(name='MyInstance')
    inst.add('node1')
    inst.add('node2')
    inst.set_data(pyblish.backend.config.identifier, value=True)

    assert len(ctx) == 1

    for selector in pyblish.backend.plugin.discover(
            'selectors', regex='SelectInstances$'):
        selector().process_all(context=ctx)

    # At least one plugin will append a selector
    assert inst in ctx
    assert len(ctx) > 1


@with_setup(setup, teardown)
def test_plugins_by_instance():
    """Returns plugins compatible with instance"""
    inst = pyblish.backend.plugin.Instance('TestInstance')
    inst.set_data(pyblish.backend.config.identifier, value=True)
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value='python')

    plugins = pyblish.backend.plugin.discover('validators')
    compatible = pyblish.backend.plugin.plugins_by_instance(plugins, inst)

    # The filter will discard at least one plugin
    assert len(plugins) > len(list(compatible))


@with_setup(setup, teardown)
def test_instances_by_plugin():
    """Returns instances compatible with plugin"""
    ctx = pyblish.backend.plugin.Context()

    # Generate two instances, only one of which will be
    # compatible with the given plugin below.
    families = (FAMILY, 'test.other_family')
    for family in families:
        inst = ctx.create_instance(
            name='TestInstance{0}'.format(families.index(family) + 1))

        inst.set_data(pyblish.backend.config.identifier, value=True)
        inst.set_data('family', value=family)
        inst.set_data('host', value='python')

        ctx.add(inst)

    plugins = pyblish.backend.plugin.discover('validators')
    plugins_dict = dict()

    for plugin in plugins:
        plugins_dict[plugin.__name__] = plugin

    plugin = plugins_dict['ValidateInstance']

    compatible = pyblish.backend.plugin.instances_by_plugin(
        instances=ctx, plugin=plugin)

    # This plugin is only compatible with
    # the family is "TestInstance1"
    assert compatible[0].name == 'TestInstance1'


@with_setup(setup, teardown)
def test_print_plugin():
    """Printing plugin returns name of class"""
    plugins = pyblish.backend.plugin.discover('validators')
    plugin = plugins[0]
    assert plugin.__name__ in repr(plugin())
    assert plugin.__name__ == str(plugin())


@with_setup(setup, teardown)
def test_name_override():
    """Instances return either a data-member of name or its native name"""
    inst = pyblish.backend.plugin.Instance(name='my_name')
    assert inst.data('name') == 'my_name'

    inst.set_data('name', value='overridden_name')
    assert inst.data('name') == 'overridden_name'


@with_setup(setup_duplicate, teardown)
def test_no_duplicate_plugins():
    """Discovering plugins results in a single occurence of each plugin"""

    plugins = pyblish.backend.plugin.discover(type='selectors')

    # There are two plugins available, but one of them is
    # hidden under the duplicate module name. As a result,
    # only one of them is returned. A log message is printed
    # to alert the user.
    assert len(plugins) == 1
