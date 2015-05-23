"""Mockup of potential integration with 3rd-party task managment suite"""


import pyblish.api
from pyblish.vendor import mock

api = mock.MagicMock()


class ConformInstancesFail(pyblish.api.Conformer):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        raise ValueError("Test fail")
