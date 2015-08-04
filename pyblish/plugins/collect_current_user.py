
import getpass
import pyblish.api


class CollectCurrentUser(pyblish.api.Collector):
    """Inject the currently logged on user into the Context"""

    def process(self, context):
        context.set_data('user', value=getpass.getuser())
