
# Standard library
import os
import random

# Local library
from pyblish import api, _plugin, _logic

from .lib import (
    setup,
    teardown,
    setup_duplicate,
    setup_empty
)
from nose.tools import (
    with_setup,
    assert_equals,
    assert_true,
    assert_raises
)


@with_setup(setup, teardown)
def test_print_plugin():
    """Printing plugin returns name of class"""
    plugins = _plugin.discover('validators')
    plugin = plugins[0]
    assert plugin.__name__ in repr(plugin())
    assert plugin.__name__ == str(plugin())


@with_setup(setup, teardown)
def test_name_override():
    """Instances return either a data-member of name or its native name"""
    inst = _plugin.Instance(name='my_name')
    assert inst.data('name') == 'my_name'

    inst.set_data('name', value='overridden_name')
    assert inst.data('name') == 'overridden_name'


@with_setup(setup_duplicate, teardown)
def test_no_duplicate_plugins():
    """Discovering plugins results in a single occurence of each plugin"""
    plugin_paths = _plugin.plugin_paths()
    assert_equals(len(plugin_paths), 2)

    plugins = _plugin.discover(type='selectors')

    # There are two plugins available, but one of them is
    # hidden under the duplicate module name. As a result,
    # only one of them is returned. A log message is printed
    # to alert the user.
    assert_equals(len(plugins), 1)


def test_entities_prints_nicely():
    """Entities Context and Instance prints nicely"""
    ctx = _plugin.Context()
    inst = ctx.create_instance(name='Test')
    assert 'Instance' in repr(inst)
    assert '_plugin' in repr(inst)


def test_deregister_path():
    path = "/server/plugins"
    _plugin.register_plugin_path(path)
    assert path in _plugin.registered_paths()
    _plugin.deregister_plugin_path(path)
    assert path not in _plugin.registered_paths()


def test_environment_paths():
    """Registering via the environment works"""
    key = "PYBLISHPLUGINPATH"
    path = '/test/path'
    existing = os.environ.get(key)

    try:
        os.environ[key] = path
        assert path in _plugin.plugin_paths()
    finally:
        os.environ[key] = existing or ''


def test_instances_by_plugin_invariant():
    ctx = _plugin.Context()
    for i in range(10):
        inst = ctx.create_instance(name="Instance%i" % i)
        inst.set_data("family", "A")

        if i % 2:
            # Every other instance is of another family
            inst.set_data("family", "B")

    class MyPlugin(_plugin.Validator):
        hosts = ["python"]
        families = ["A"]

        def process(self, instance):
            pass

    compatible = _logic.instances_by_plugin(ctx, MyPlugin)

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
                   (api.Validator,),
                   {"families": ["myFamily"]})
    Plugin2 = type("Plugin2",
                   (api.Validator,),
                   {"families": ["*"]})

    assert Plugin2 in api.plugins_by_family(
        [Plugin1, Plugin2], "myFamily")


@with_setup(setup, teardown)
def test_plugins_sorted():
    """Plug-ins are returned sorted by their `order` attribute"""
    plugins = api.discover()
    random.shuffle(plugins)  # Randomise their order
    api.sort_plugins(plugins)

    order = 0
    for plugin in plugins:
        assert_true(plugin.order >= order)
        order = plugin.order

    assert order > 0, plugins


@with_setup(setup_empty, teardown)
def test_inmemory_plugins():
    """In-memory plug-ins works fine"""

    class InMemoryPlugin(api.Selector):
        hosts = ["*"]
        families = ["*"]

        def process_context(self, context):
            context.set_data("workingFine", True)

    api.register_plugin(InMemoryPlugin)

    context = api.Context()
    for result in _logic.process(
            func=_plugin.process,
            plugins=api.discover,
            context=context):
        assert_true(result["plugin"].id == InMemoryPlugin.id)

    assert context.data("workingFine") is True


@with_setup(setup_empty, teardown)
def test_inmemory_query():
    """Asking for registered plug-ins works well"""

    InMemoryPlugin = type("InMemoryPlugin", (api.Selector,), {})
    api.register_plugin(InMemoryPlugin)
    assert api.registered_plugins()[0].id == InMemoryPlugin.id


@with_setup(setup_empty, teardown)
def test_plugin_families_defaults():
    """Plug-ins without specific families default to wildcard"""

    class SelectInstances(api.Selector):
        def process(self, instance):
            pass

    instance = api.Instance("MyInstance")
    instance.set_data("family", "SomeFamily")

    assert_equals(api.instances_by_plugin(
        [instance], SelectInstances)[0], instance)

    class ValidateInstances(api.Validator):
        def process(self, instance):
            pass

    assert_equals(api.instances_by_plugin(
        [instance], ValidateInstances)[0], instance)
