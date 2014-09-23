
import time
import pyblish.api


@pyblish.api.log
class SelectCurrentDate(pyblish.api.Selector):
    """Inject the current time into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        """Formatting is coming from configuration"""
        date = time.strftime(pyblish.api.config['date_format'])
        context.set_data('date', value=date)
