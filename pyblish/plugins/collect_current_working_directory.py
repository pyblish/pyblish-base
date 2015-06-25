
import os
import pyblish.api


@pyblish.api.log
class CollectCurrentWorkingDirectory(pyblish.api.Collector):
    """Inject the current working directory into Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):
        context.set_data('cwd', value=os.getcwd())
