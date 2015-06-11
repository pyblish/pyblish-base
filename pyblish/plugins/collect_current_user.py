
import getpass
import pyblish.api


@pyblish.api.log
class CollectCurrentUser(pyblish.api.Collector):
    """Inject the currently logged on user into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):
        context.set_data('user', value=getpass.getuser())
