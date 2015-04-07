import sys
import pyblish.lib

from pyblish.vendor.nose.tools import *


def test_where():
    """lib.where works fine"""
    exe = pyblish.lib.where("python")
    assert_equals(sys.executable.lower(), exe.lower())
