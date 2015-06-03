
import pyblish.api
import pyblish.lib


@pyblish.api.log
class SelectCurrentDate(pyblish.api.Selector):
    """Inject the current time into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):
        """Formatting is coming from configuration"""
        date = pyblish.lib.time()
        context.set_data('date', value=date)
