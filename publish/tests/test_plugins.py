
# Standard library
import os

# Local library
import publish.plugin
import publish.config

from publish.vendor.nose.tools import raises

# Setup
HOST = 'python'
FAMILY = 'test.family'

plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')

publish.plugin.deregister_all()
publish.plugin.register_plugin_path(plugin_path)


def test_selection_interface():
    """The interface of selection works fine"""

    ctx = publish.plugin.Context()

    selectors = publish.plugin.discover(type='selectors')
    assert len(selectors) >= 1

    for selector in selectors:
        if not HOST in selector.hosts:
            continue
        selector().process(ctx)

    assert len(ctx) >= 1

    inst = ctx.pop()
    assert len(inst) >= 3


def test_validation_interface():
    """The interface of validation works fine"""
    ctx = publish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.plugin.Instance('test_instance')
    inst.add('test_node1_PLY')
    inst.add('test_node2_PLY')
    inst.add('test_node3_GRP')
    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    validators = publish.plugin.discover(type='validators')
    assert len(validators) >= 1

    for validator in validators:
        validator().process(ctx)


@raises(ValueError)
def test_validation_failure():
    """Validation throws exception upon failure"""
    ctx = publish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.plugin.Instance('test_instance')

    inst.add('test_PLY')
    inst.add('test_misnamed')

    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    validators = publish.plugin.discover(type='validators')
    assert len(validators) >= 1

    for validator in validators:
        validator().process(ctx)


def test_extraction_interface():
    """The interface of extractors works fine"""
    ctx = publish.plugin.Context()

    # Manually create instance and nodes, bypassing selection
    inst = publish.plugin.Instance('test_instance')

    inst.add('test_PLY')
    inst.config[publish.config.identifier] = True
    inst.config['family'] = FAMILY

    ctx.add(inst)

    # Assuming validations pass

    extractors = publish.plugin.discover(type='extractors')
    assert len(extractors) >= 1

    for extractor in extractors:
        extractor().process(ctx)


def test_extraction_failure():
    """Extraction fails ok

    When extraction fails, it is imperitative that other extractors
    keep going and that the user is properly notified of the failure.

    """


def test_plugin_interface():
    """All plugins share interface"""

    ctx = publish.plugin.Context()

    for plugin in publish.plugin.discover():
        plugin().process(ctx)

    print ctx


def test_selection_appends():
    """Selectors append, rather than replace existing instances"""

    ctx = publish.plugin.Context()

    my_inst = publish.plugin.Instance('MyInstance')
    my_inst.add('node1')
    my_inst.add('node2')
    my_inst.config[publish.config.identifier] = True

    ctx.add(my_inst)

    assert len(ctx) == 1

    for selector in publish.plugin.discover('selectors'):
        selector().process(context=ctx)

    # At least one plugin will append a selector
    assert my_inst in ctx
    assert len(ctx) > 1


if __name__ == '__main__':
    import logging
    import publish
    log = publish.setup_log()
    log.setLevel(logging.DEBUG)

    # test_selection_interface()
    # test_validation_interface()
    # test_validation_failure()
    # test_extraction_interface()
    # test_plugin_interface()
    test_selection_appends()
