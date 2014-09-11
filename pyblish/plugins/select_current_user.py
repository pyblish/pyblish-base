"""Inject the currently logged on user into the Context"""

import getpass

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectCurrentUser(pyblish.backend.plugin.Selector):
    """Append the currently logged on user"""

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):
        context.set_data('user', value=getpass.getuser())
