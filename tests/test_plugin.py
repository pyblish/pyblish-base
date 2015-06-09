import os
import sys
import shutil
import tempfile
import contextlib

import pyblish.plugin
from pyblish.vendor.nose.tools import (
    with_setup,
    assert_true,
    assert_equals,
)

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
    """Plug-ins don't linger after a second discovery

    E.g. when changing the name of a plug-in and then rediscover
    the previous plug-ins is still around.

    """

    with tempdir() as temp:
        print("Writing temporarily to: %s" % temp)
        module = os.path.join(temp, "selector.py")
        pyblish.api.register_plugin_path(temp)

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MySelector(pyblish.api.Selector):
    pass
""")

        with open(module) as f:
            print("File contents after first write:")
            print(f.read())

        # MySelector should be accessible by now
        plugins = [p.__name__ for p in pyblish.api.discover()]

        assert "MySelector" in plugins, plugins
        assert "MyOtherSelector" not in plugins, plugins

        # Remove module, and it's .pyc equivalent
        [os.remove(os.path.join(temp, fname))
         for fname in os.listdir(temp)]

        with open(module, "w") as f:
            f.write("""
import pyblish.api

class MyOtherSelector(pyblish.api.Selector):
    pass
""")

        with open(module) as f:
            print("File contents after second write:")
            print(f.read())

        # MySelector should be gone in favour of MyOtherSelector
        plugins = [p.__name__ for p in pyblish.api.discover()]

        assert "MyOtherSelector" in plugins, plugins
        assert "MySelector" not in plugins, plugins


@with_setup(lib.setup_empty, lib.teardown)
def test_unsupported_host():
    """Publishing from within an unsupported host is ok"""

    class Always(pyblish.api.Plugin):
        """This plug-in is always discoverable"""

    class OnlyInUnknown(pyblish.api.Plugin):
        """This plug-in is only discoverable from unknown hosts"""
        hosts = ["unknown"]

    class OnlyInMaya(pyblish.api.Plugin):
        """This plug-in is only discoverable from maya"""
        hosts = ["maya"]


    pyblish.api.register_plugin(Always)
    pyblish.api.register_plugin(OnlyInUnknown)
    pyblish.api.register_plugin(OnlyInMaya)

    discovered = pyblish.api.discover()

    assert Always in discovered
    assert OnlyInUnknown not in discovered  # It's known to be python
    assert OnlyInMaya not in discovered  # Host is not  maya

    def _current_host():
        return "maya"

    try:
        old = sys.executable
        sys.executable = "/root/some_executable"
        
        discovered = pyblish.api.discover()
        assert OnlyInUnknown in discovered
        assert OnlyInMaya not in discovered

    finally:
        sys.executable = old

    try:
        old = sys.executable
        sys.executable = "/root/maya"
        
        discovered = pyblish.api.discover()
        assert OnlyInUnknown not in discovered
        assert OnlyInMaya in discovered

    finally:
        sys.executable = old


@with_setup(lib.setup_empty, lib.teardown)
def test_temporarily_disabled_plugins():
    """Plug-ins as files starting with an underscore are hidden"""

    discoverable = """
import pyblish.api

class Discoverable(pyblish.api.Plugin):
    pass
"""

    notdiscoverable = """
import pyblish.api

class NotDiscoverable(pyblish.api.Plugin):
    pass
"""

    with tempdir() as d:
        pyblish.api.register_plugin_path(d)

        with open(os.path.join(d, "discoverable.py"), "w") as f:
            f.write(discoverable)

        with open(os.path.join(d, "_undiscoverable.py"), "w") as f:
            f.write(notdiscoverable)


        plugins = [p.__name__ for p in pyblish.api.discover()]
        assert "Discoverable" in plugins
        assert "NotDiscoverable" not in plugins
