"""This plugin is incomplete and can't be used"""

import pyblish.api


@pyblish.api.log
class ValidateMissingFamilies(pyblish.api.Validator):
    """Select instances"""

    hosts = ['python']
    version = (0, 1, 0)
