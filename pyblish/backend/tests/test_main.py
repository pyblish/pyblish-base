import pyblish.main
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
    # test_main_interface()
