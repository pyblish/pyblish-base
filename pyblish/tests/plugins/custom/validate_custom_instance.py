"""Mockup of potential integration with 3rd-party task managment suite"""

import pyblish.api


class ValidateCustomInstance(pyblish.api.Validator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)
