import os
import shutil
import tempfile
import contextlib

import pyblish.plugin
from pyblish.vendor.nose.tools import *

import lib


@contextlib.contextmanager
def tempdir():
    try:
        tempdir = tempfile.mkdtemp()
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def test_unique_id():
    """Plug-ins and instances have a unique id"""

    class MyPlugin(pyblish.plugin.Selector):
        pass

    assert_true(hasattr(MyPlugin, "id"))

    instance = pyblish.plugin.Instance("MyInstance")
    assert_true(hasattr(instance, "id"))


def test_context_from_instance():
    """Instances provide access to their parent context"""

    context = pyblish.plugin.Context()
    instance = context.create_instance("MyInstance")
    assert_equals(context, instance.context)


def test_legacy():
    """Legacy is determined by existing process_* methods"""
    class LegacyPlugin(pyblish.plugin.Selector):
        def process_context(self, context):
            pass

    class NotLegacyPlugin(pyblish.plugin.Selector):
        def process(self, context):
            pass

    assert_true(hasattr(LegacyPlugin, "__pre11__"))
    assert_equals(LegacyPlugin.__pre11__, True)
    assert_true(hasattr(NotLegacyPlugin, "__pre11__"))
    assert_equals(NotLegacyPlugin.__pre11__, False)


def test_asset():
    """Using asset over instance works fine"""
    context = pyblish.plugin.Context()
    
    asseta = context.create_asset("MyAssetA", family="myFamily")
    assetb = context.create_asset("MyAssetB", family="myFamily")

    assert_true(asseta in context)
    assert_true(assetb in context)


@with_setup(lib.setup_empty, lib.teardown)
def test_import_mechanism_duplication():
    """Altering a plug-in after it has been loaded once merges old and new"""

    with tempdir() as temp:
        module = os.path.join(temp, "selector.py")
        pyblish.api.register_plugin_path(temp)

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MySelector(pyblish.api.Selector):
    pass
""")

        # MySelector should be accessible by now
        plugins = pyblish.api.discover()

        assert_true("MySelector" in [p.__name__ for p in plugins])
        assert_false("MyOtherSelector" in [p.__name__ for p in plugins])

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MyOtherSelector(pyblish.api.Selector):
    pass
""")

        # MySelector should be gone in favour of MyOtherSelector

        plugins = pyblish.api.discover()

        assert_false("MySelector" in [p.__name__ for p in plugins])
        assert_true("MyOtherSelector" in [p.__name__ for p in plugins])
