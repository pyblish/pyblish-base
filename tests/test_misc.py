import os
import tempfile

from . import lib

import pyblish.lib
import pyblish.compat
from pyblish.vendor.nose.tools import *


def test_where():
    """where() works fine"""

    oldpath = os.environ["PATH"]

    # Create fixture with executables
    temp = tempfile.mkdtemp()
    for fname in ("myfile.exe", "notexec.bin", "test.bat"):
        with open(os.path.join(temp, fname), "w") as f:
            f.write("")

    os.environ["PATH"] = temp + ";"

    myfile = pyblish.lib.where("myfile")
    assert_equals(os.path.basename(myfile).lower(), "myfile.exe")
    
    notexec = pyblish.lib.where("notexec")
    assert_equals(notexec, None)


@with_setup(lib.setup, lib.teardown)
def test_compat():
    """Using compatibility functions works"""
    pyblish.compat.sort([])
    pyblish.compat.deregister_all()
