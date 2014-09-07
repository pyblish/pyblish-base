
import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectInstancesError(pyblish.backend.plugin.Selector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        raise ValueError("Test exception")
