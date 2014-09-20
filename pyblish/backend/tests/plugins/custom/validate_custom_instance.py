"""Mockup of potential integration with 3rd-party task managment suite"""

import pyblish


class ValidateCustomInstance(pyblish.Validator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)
