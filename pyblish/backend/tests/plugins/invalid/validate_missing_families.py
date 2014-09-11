"""This plugin is incomplete and can't be used"""

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ValidateMissingFamilies(pyblish.backend.plugin.Validator):
    """Select instances"""

    hosts = ['python']
    version = (0, 1, 0)
