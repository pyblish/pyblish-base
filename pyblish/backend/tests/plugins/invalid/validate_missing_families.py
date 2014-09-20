"""This plugin is incomplete and can't be used"""

import pyblish


@pyblish.log
class ValidateMissingFamilies(pyblish.Validator):
    """Select instances"""

    hosts = ['python']
    version = (0, 1, 0)
