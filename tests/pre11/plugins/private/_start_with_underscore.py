import pyblish.plugin

class MyPrivatePlugin(pyblish.plugin.Collector):

    hosts = ["*"]
    version = (0, 1, 0)

    def process_context(self, context):
        pass

raise Exception("This should not be executed, plugin loading should be skipped")