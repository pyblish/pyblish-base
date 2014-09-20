
import getpass
import pyblish


@pyblish.log
class SelectCurrentUser(pyblish.Selector):
    """Inject the currently logged on user into the Context"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('user', value=getpass.getuser())
