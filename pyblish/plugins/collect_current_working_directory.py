
import os
import pyblish.api


class CollectCurrentWorkingDirectory(pyblish.api.Collector):
    """Inject the current working directory into Context"""

    def process(self, context):
        context.data['cwd'] = os.getcwd()
