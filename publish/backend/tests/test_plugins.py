
# Standard library
import os

# Local library
import publish.config
import publish.backend.plugin

from publish.vendor.nose.tools import raises

# Setup
HOST = 'python'
FAMILY = 'test.family'

plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')

publish.backend.plugin.deregister_all()
publish.backend.plugin.register_plugin_path(plugin_path)


def test_selection_interface():
    """The interface of selection works fine"""

    ctx = publish.backend.plugin.Context()

    selectors = publish.backend.plugin.discover(type='selectors')
    assert len(selectors) >= 1

    for selector in selectors:
        if not HOST in selector.hosts:
            continue

        for instance, error in selector().process(ctx):
            assert error is None

    assert len(ctx) >= 1

    inst = ctx.pop()
    assert len(inst) >= 3


def test_validation_interface():
    """The interface of validation works fine"""
    ctx = publish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.backend.plugin.Instance('test_instance')
    inst.add('test_node1_PLY')
    inst.add('test_node2_PLY')
    inst.add('test_node3_GRP')
    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    validators = publish.backend.plugin.discover(type='validators')
    assert len(validators) >= 1

    for validator in validators:
        for instance, error in validator().process(ctx):
            assert error is None


@raises(ValueError)
def test_validation_failure():
    """Validation throws exception upon failure"""
    ctx = publish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.backend.plugin.Instance('test_instance')

    inst.add('test_PLY')
    inst.add('test_misnamed')

    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    validators = publish.backend.plugin.discover(type='validators',
                                                 regex='ValidateInstance')
    assert len(validators) == 1

    for validator in validators:
        for instance, error in validator().process(ctx):
            raise error


def test_extraction_interface():
    """The interface of extractors works fine"""
    ctx = publish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.backend.plugin.Instance('test_instance')

    inst.add('test_PLY')
    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    # Assuming validations pass

    extractors = publish.backend.plugin.discover(type='extractors',
                                                 regex='.*ExtractInstances$')
    extractor = extractors.pop()
    assert extractor.__name__ == "ExtractInstances"

    for instance, error in extractor().process(ctx):
        assert error is None


@raises(ValueError)
def test_extraction_failure():
    """Extraction fails ok

    When extraction fails, it is imperitative that other extractors
    keep going and that the user is properly notified of the failure.

    """
    ctx = publish.backend.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.backend.plugin.Instance('test_instance')

    inst.add('test_PLY')
    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    # Assuming validations pass

    extractors = publish.backend.plugin.discover(type='extractors',
                                                 regex='.*Fail$')
    extractor = extractors.pop()
    assert extractor.__name__ == "ExtractInstancesFail"

    for instance, error in extractor().process(ctx):
        raise error


def test_plugin_interface():
    """All plugins share interface"""

    ctx = publish.backend.plugin.Context()

    for plugin in publish.backend.plugin.discover():
        plugin().process(ctx)

    print ctx


def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    ctx = publish.backend.plugin.Context()

    my_inst = publish.backend.plugin.Instance('MyInstance')
    my_inst.add('node1')
    my_inst.add('node2')
    my_inst.config[publish.config.identifier] = True

    ctx.add(my_inst)

    assert len(ctx) == 1

    for selector in publish.backend.plugin.discover('selectors'):
        for instance, error in selector().process(context=ctx):
            assert error is None

    # At least one plugin will append a selector
    assert my_inst in ctx
    assert len(ctx) > 1


def test_plugins_by_instance():
    """Returns plugins compatible with instance"""
    inst = publish.backend.plugin.Instance('TestInstance')
    inst.config['family'] = 'test.family'
    inst.config['host'] = 'python'
    inst.config[publish.config.identifier] = True

    plugins = publish.backend.plugin.discover('validators')
    compatible = publish.backend.plugin.plugins_by_instance(plugins, inst)

    # The filter will discard at least one plugin
    assert len(plugins) > len(list(compatible))


def test_instances_by_plugin():
    """Returns instances compatible with plugin"""
    ctx = publish.backend.plugin.Context()

    # Generate two instances, only one of which will be
    # compatible with the given plugin below.
    for family in ('test.family', 'test.other_family'):
        inst = publish.backend.plugin.Instance('TestInstance')
        inst.config['family'] = family
        inst.config['host'] = 'python'
        inst.config[publish.config.identifier] = True

        ctx.add(inst)

    plugins = publish.backend.plugin.discover('validators')
    plugins_dict = dict()

    for plugin in plugins:
        plugins_dict[plugin.__name__] = plugin

    # This plugin is only compatible with family = test.family
    plugin = plugins_dict['ValidateInstance']

    compatible = publish.backend.plugin.instances_by_plugin(
        instances=ctx, plugin=plugin)

    assert next(compatible).name == 'TestInstance'


if __name__ == '__main__':
    import logging
    import publish
    log = publish.setup_log()
    log.setLevel(logging.DEBUG)

    test_selection_interface()
    test_validation_interface()
    test_validation_failure()
    test_extraction_interface()
    test_extraction_failure()
    test_plugin_interface()
    test_selection_appends()
    test_plugins_by_instance()
    test_instances_by_plugin()
