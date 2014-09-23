
import os
import pyblish.api


@pyblish.api.log
class SelectCurrentWorkingDirectory(pyblish.api.Selector):
    """Inject the current working directory into Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('cwd', value=os.getcwd())
