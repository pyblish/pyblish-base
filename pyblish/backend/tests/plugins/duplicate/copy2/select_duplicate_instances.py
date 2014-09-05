
import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectDuplicateInstance2(pyblish.backend.plugin.Selector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        pass
