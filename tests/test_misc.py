from . import lib

import pyblish.lib
import pyblish.compat
from nose2.tools.decorators import (
    with_setup,
    with_teardown
)


@with_setup(lib.setup)
@with_teardown(lib.teardown)
def test_compat():
    """Using compatibility functions works"""
    pyblish.compat.sort([])
    pyblish.compat.deregister_all()
