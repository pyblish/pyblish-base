
import getpass
import pyblish.api


@pyblish.api.log
class SelectCurrentUser(pyblish.api.Selector):
    """Inject the currently logged on user into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('user', value=getpass.getuser())
