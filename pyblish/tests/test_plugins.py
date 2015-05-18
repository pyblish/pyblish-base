
# Standard library
import os
import random

# Local library
from . import lib
import pyblish.plugin

from pyblish.vendor import mock

from pyblish.tests.lib import (
    setup, teardown, setup_duplicate, setup_invalid,
    setup_empty, FAMILY)
from pyblish.vendor.nose.tools import *


def test_plugins_by_family():
    """plugins_by_family works fine"""
    Plugin1 = type("Plugin1", (pyblish.api.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.api.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    assert_equals(pyblish.plugin.plugins_by_family(
                  (Plugin1, Plugin2), family="a"),
                  [Plugin1])


def test_plugins_by_host():
    """plugins_by_host works fine."""
    Plugin1 = type("Plugin1", (pyblish.api.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.api.Validator,), {})

    Plugin1.hosts = ["a"]
    Plugin2.hosts = ["b"]

    assert_equals(pyblish.plugin.plugins_by_host(
                  (Plugin1, Plugin2), host="a"),
                  [Plugin1])


def test_plugins_by_instance():
    """plugins_by_instance works fine."""
    Plugin1 = type("Plugin1", (pyblish.api.Validator,), {})
    Plugin2 = type("Plugin2", (pyblish.api.Validator,), {})

    Plugin1.families = ["a"]
    Plugin2.families = ["b"]

    instance = pyblish.api.Instance("A")
    instance.set_data("family", "a")

    assert_equals(pyblish.plugin.plugins_by_instance(
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
    path = "/server/plugins"
    pyblish.plugin.register_plugin_path(path)
    assert path in pyblish.plugin.registered_paths()
    pyblish.plugin.deregister_plugin_path(path)
    assert path not in pyblish.plugin.registered_paths()


def test_environment_paths():
    """Registering via the environment works"""
    key = lib.config['paths_environment_variable']
    path = '/test/path'
    existing = os.environ.get(key)

    try:
        os.environ[key] = path
        assert path in pyblish.plugin.plugin_paths()
    finally:
        os.environ[key] = existing or ''


@raises(ValueError)
def test_discover_invalid_type():
    """Discovering an invalid type raises an error"""
    pyblish.plugin.discover(type='INVALID')


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


def test_plugins_by_family_wildcard():
    """Plug-ins with wildcard family is included in every query"""
    Plugin1 = type("Plugin1",
                   (pyblish.api.Validator,),
                   {"families": ["myFamily"]})
    Plugin2 = type("Plugin2",
                   (pyblish.api.Validator,),
                   {"families": ["*"]})

    assert Plugin2 in pyblish.api.plugins_by_family(
        [Plugin1, Plugin2], "myFamily")


@with_setup(setup, teardown)
def test_plugins_sorted():
    """Plug-ins are returned sorted by their `order` attribute"""
    plugins = pyblish.api.discover()
    random.shuffle(plugins)  # Randomise their order
    pyblish.api.sort_plugins(plugins)

    order = 0
    for plugin in plugins:
        assert_true(plugin.order >= order)
        order = plugin.order

    assert order > 0, plugins


@with_setup(setup_empty, teardown)
def test_inmemory_plugins():
    """In-memory plug-ins works fine"""

    class InMemoryPlugin(pyblish.api.Selector):
        hosts = ["*"]
        families = ["*"]

        def process_context(self, context):
            context.set_data("workingFine", True)

    pyblish.api.register_plugin(InMemoryPlugin)

    context = pyblish.api.Context()
    for plugin in pyblish.api.discover():
        assert plugin is InMemoryPlugin
        plugin().process_context(context)

    assert context.data("workingFine") is True


@with_setup(setup_empty, teardown)
def test_inmemory_query():
    """Asking for registered plug-ins works well"""

    InMemoryPlugin = type("InMemoryPlugin", (pyblish.api.Selector,), {})
    pyblish.api.register_plugin(InMemoryPlugin)
    assert pyblish.api.registered_plugins()[0] == InMemoryPlugin


@with_setup(setup_empty, teardown)
def test_plugin_families_defaults():
    """Plug-ins without specific families default to wildcard"""

    class SelectInstances(pyblish.api.Selector):
        pass

    instance = pyblish.api.Instance("MyInstance")
    instance.set_data("family", "SomeFamily")

    assert_equals(pyblish.api.instances_by_plugin(
        [instance], SelectInstances)[0], instance)

    class ValidateInstances(pyblish.api.Validator):
        pass

    assert_equals(pyblish.api.instances_by_plugin(
        [instance], ValidateInstances)[0], instance)


@with_setup(setup_empty, teardown)
def test_inmemory_discover_filtering():
    """Filtering using discover() works with in-memory plug-ins"""

    class SelectInstances(pyblish.api.Selector):
        pass

    class ValidateInstances(pyblish.api.Validator):
        pass

    class ExtractInstances(pyblish.api.Extractor):
        pass

    class ConformInstances(pyblish.api.Conformer):
        pass

    for plugin in (SelectInstances,
                   ValidateInstances,
                   ExtractInstances,
                   ConformInstances):
        pyblish.api.register_plugin(plugin)

    for type, plugin in {"selectors": SelectInstances,
                         "validators": ValidateInstances,
                         "extractors": ExtractInstances,
                         "conformers": ConformInstances}.items():
        print "Comparing %s with type: %s" % (plugin, type)
        discovered = pyblish.plugin.discover(type=type)
        print "Discovered: %s" % discovered
        assert_equals(discovered[0], plugin)

    assert_equals(
        pyblish.plugin.discover(regex="^Extract"),
        [ExtractInstances])
