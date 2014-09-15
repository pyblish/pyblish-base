"""Inject the current time into the Context"""

import time

import pyblish.backend.lib
import pyblish.backend.plugin
import pyblish.backend.config


@pyblish.backend.lib.log
class SelectCurrentDate(pyblish.backend.plugin.Selector):
    """Append the currently working directory"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        """Formatting is coming from configuration"""
        date = time.strftime(pyblish.backend.config.date_format)
        context.set_data('date', value=date)
