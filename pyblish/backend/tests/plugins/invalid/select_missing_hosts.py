"""This plugin is incomplete and can't be used"""

import pyblish


@pyblish.log
class SelectMissingHosts(pyblish.Selector):
    """Select instances"""

    version = (0, 1, 0)

    def process_context(self, context):
        pass
