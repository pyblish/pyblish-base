
import getpass
import pyblish.api


class CollectCurrentUser(pyblish.api.ContextPlugin):
    """Inject the currently logged on user into the Context"""

    order = pyblish.api.CollectorOrder

    def process(self, context):
        context.data['user'] = getpass.getuser()
