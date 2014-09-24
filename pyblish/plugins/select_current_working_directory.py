
import os
import pyblish


@pyblish.log
class SelectCurrentWorkingDirectory(pyblish.Selector):
    """Inject the current working directory into Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('cwd', value=os.getcwd())
