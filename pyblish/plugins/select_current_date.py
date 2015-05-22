
import pyblish.api
import pyblish.util


@pyblish.api.log
class SelectCurrentDate(pyblish.api.Selector):
    """Inject the current time into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        """Formatting is coming from configuration"""
        date = pyblish.util.time()
        context.set_data('date', value=date)
