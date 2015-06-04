"""This plugin is incomplete and can't be used"""

import pyblish.api


@pyblish.api.log
class SelectMissingHosts(pyblish.api.Selector):
    """Select instances"""

    requires = False
    version = "Invalid"
