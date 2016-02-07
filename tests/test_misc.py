from . import lib

import pyblish.lib
import pyblish.compat
from nose.tools import (
    with_setup
)


@with_setup(lib.setup, lib.teardown)
def test_compat():
    """Using compatibility functions works"""
    pyblish.compat.sort([])
    pyblish.compat.deregister_all()
