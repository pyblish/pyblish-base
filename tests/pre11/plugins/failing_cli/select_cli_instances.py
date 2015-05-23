import pyblish.api


@pyblish.api.log
class SelectCliInstances(pyblish.api.Selector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        raise ValueError(context.data("fail"))
