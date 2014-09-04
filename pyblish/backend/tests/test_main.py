import os
import json

import pyblish.main
import pyblish.backend.lib
import pyblish.backend.config
import pyblish.backend.plugin

HOST = 'python'
FAMILY = 'test.family'


def test_main_interface_with_empty_context():
    """Interface of pyblish.main works event if context is empty"""
    ctx = pyblish.backend.plugin.Context()

    assert pyblish.main.select(ctx) is None
    assert pyblish.main.validate(ctx) is None
    assert pyblish.main.extract(ctx) is None
    assert pyblish.main.conform(ctx) is None


def test_config():
    config = pyblish.backend.config
    config_path = pyblish.backend.lib.main_package_path()
    config_path = os.path.join(config_path, 'backend', 'config.json')
    with open(config_path) as f:
        manual_config = json.load(f)

    for key, value in manual_config.iteritems():
        assert getattr(config, key) == value


# def test_main_interface():
#     inst = pyblish.backend.plugin.Instance(name='Test')
#     inst.add('TestNode1')
#     inst.add('TestNode2')
#     inst.add('TestNode3')
#     inst.set_data('family', value=FAMILY)
#     inst.set_data('publishable', value=True)

#     ctx = pyblish.backend.plugin.Context()
#     ctx.add(inst)

#     raise NotImplementedError


if __name__ == '__main__':
    import logging
    import pyblish
    log = pyblish.setup_log()
    log.setLevel(logging.DEBUG)

    test_main_interface_with_empty_context()
    test_config()
    # test_main_interface()
