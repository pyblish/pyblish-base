
import pyblish.api
import pyblish.lib


class CollectCurrentDate(pyblish.api.Collector):
    """Inject the current time into the Context"""

    def process(self, context):
        """Formatting is coming from configuration"""
        date = pyblish.lib.time()
        context.data['date'] = date
