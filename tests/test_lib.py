import sys
import functools

import pyblish.lib

from nose.tools import (
    with_setup,
    assert_equals,
)

from .lib import setup_empty


def test_weak_method():
    """Weak references work with instancemethod"""
    
    count = {"#": 0}

    class Object(object):
        def func(self):
            count["#"] += 1
            
    o = Object()
    wo = pyblish.lib.WeakRef(o.func)
    
    assert count["#"] == 0
    wo()()
    assert count["#"] == 1
    
    del(o)
    
    assert wo() is None, wo()


def test_weak_function():
    """WeakRef works with functions"""
    
    count = {"#": 0}

    def func():
        count["#"] += 1

    fo = pyblish.lib.WeakRef(func)
    
    assert count["#"] == 0
    fo()()
    assert count["#"] == 1, fo()
    
    del(func)

    assert fo() is None, fo
