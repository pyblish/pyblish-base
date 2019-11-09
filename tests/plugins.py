"""Plugins for testing purposes.

Source them like this from within a test function:

api.deregister_all_paths()
api.register_plugin_path(os.path.dirname(__file__))

This ensures that the plugins are actually loaded through `plugin.discover`.
"""
from pyblish import api


class FailingExplicitPlugin(api.InstancePlugin):
    """Raise an exception."""

    def process(self, instance):
        raise Exception("A test exception")


class FailingImplicitPlugin(api.Validator):
    """Raise an exception."""

    def process(self, instance):
        raise Exception("A test exception")
