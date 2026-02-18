import pyblish.lib
import pyblish.compat


def test_compat(setup_and_teardown):
    """Using compatibility functions works"""
    pyblish.compat.sort([])
    pyblish.compat.deregister_all()
