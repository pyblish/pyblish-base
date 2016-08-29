from . import lib

from pyblish import _compat
from nose.tools import (
    with_setup
)


@with_setup(lib.setup, lib.teardown)
def test_compat():
    """Using compatibility functions works"""
    _compat.sort([])
    _compat.deregister_all()
