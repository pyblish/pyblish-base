import pyblish


class SelectEcho(pyblish.Selector):
    hosts = ['*']
    version = (0, 0, 1)

    def process_context(self, context):
        print context.data()
