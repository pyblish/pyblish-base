"""Gether information about the local environment"""

import os
import getpass

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectCurrentUser(pyblish.backend.plugin.Selector):
    """Append the currently logged on user"""

    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):
        context.set_data('user', value=getpass.getuser())
        yield None, None


@pyblish.backend.lib.log
class SelectCurrentWorkingDirectory(pyblish.backend.plugin.Selector):
    """Append the currently working directory"""

    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):
        context.set_data('cwd', value=os.getcwd())
        yield None, None
