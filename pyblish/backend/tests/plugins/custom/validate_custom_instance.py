"""Mockup of potential integration with 3rd-party task managment suite"""


import pyblish.backend.plugin


class ValidateCustomInstance(pyblish.backend.plugin.Validator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)
