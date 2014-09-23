"""This plugin is incomplete and can't be used"""

import pyblish.api


@pyblish.api.log
class SelectMissingHosts(pyblish.api.Selector):
    """Select instances"""

    version = (0, 1, 0)

    def process_context(self, context):
        pass
