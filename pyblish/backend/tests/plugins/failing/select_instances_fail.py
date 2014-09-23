
import pyblish.api


@pyblish.api.log
class SelectInstancesError(pyblish.api.Selector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        raise ValueError("Test exception")
