import os

import pyblish.main
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin

from pyblish.vendor import yaml

from pyblish.backend.tests.lib import (
    setup, teardown, FAMILY, HOST, setup_failing)
from pyblish.vendor.nose.tools import with_setup, raises


@with_setup(setup, teardown)
def test_config():
    """Config works as expected"""
    config = pyblish.backend.config
    config_path = pyblish.backend.lib.main_package_path()
    config_path = os.path.join(config_path, 'backend', 'config.yaml')

    with open(config_path) as f:
        manual_config = yaml.load(f)

    for key, value in manual_config.iteritems():
        assert getattr(config, key) == value


@with_setup(setup, teardown)
def test_main_interface():
    """Main interface works"""
    ctx = pyblish.backend.plugin.Context()
    inst = ctx.create_instance(name='Test')

    inst.add('TestNode1_AST')
    inst.add('TestNode2_LOC')
    inst.add('TestNode3_EXT')

    inst.set_data('family', value=FAMILY)
    inst.set_data('publishable', value=True)

    pyblish.main.process_all('selectors', ctx)

    pyblish.main.select(ctx)
    pyblish.main.validate(ctx)
    pyblish.main.extract(ctx)
    pyblish.main.conform(ctx)


@with_setup(setup_failing, teardown)
def test_main_safe_processes_fail():
    """Failing selection, extraction or conform merely logs a message"""
    ctx = pyblish.backend.plugin.Context()
    pyblish.main.select(ctx)

    # Give plugins something to process
    inst = ctx.create_instance(name='TestInstance')
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value=HOST)

    pyblish.main.extract(ctx)
    pyblish.main.conform(ctx)


@raises(ValueError)
@with_setup(setup_failing, teardown)
def test_main_validation_fail():
    """Failing validation raises an exception"""
    ctx = pyblish.backend.plugin.Context()

    # Give validators something to validate
    inst = ctx.create_instance(name='TestInstance')
    inst.set_data('family', value=FAMILY)
    inst.set_data('host', value=HOST)

    pyblish.main.validate(ctx)


if __name__ == '__main__':
    import logging
    import pyblish
    log = pyblish.setup_log()
    log.setLevel(logging.DEBUG)

    # test_config()
    test_main_interface()
