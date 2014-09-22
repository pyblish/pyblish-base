
import time
import pyblish


@pyblish.log
class SelectCurrentDate(pyblish.Selector):
    """Inject the current time into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        """Formatting is coming from configuration"""
        date = time.strftime(pyblish.backend.config.date_format)
        context.set_data('date', value=date)
