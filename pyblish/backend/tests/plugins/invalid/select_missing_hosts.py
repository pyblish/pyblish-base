"""This plugin is incomplete and can't be used"""

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectMissingHosts(pyblish.backend.plugin.Selector):
    """Select instances"""

    version = (0, 1, 0)

    def process_context(self, context):
        pass
