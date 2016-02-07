
import os
import pyblish.api


class CollectCurrentWorkingDirectory(pyblish.api.ContextPlugin):
    """Inject the current working directory into Context"""

    order = pyblish.api.CollectorOrder

    def process(self, context):
        context.data['cwd'] = os.getcwd()
