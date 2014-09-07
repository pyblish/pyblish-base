"""Inject the current working directory into Context"""

import os

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectCurrentWorkingDirectory(pyblish.backend.plugin.Selector):
    """Append the currently working directory"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('cwd', value=os.getcwd())
