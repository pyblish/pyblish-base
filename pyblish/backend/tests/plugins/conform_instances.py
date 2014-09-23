"""Mockup of potential integration with 3rd-party task managment suite"""

import pyblish.api
from pyblish.vendor import mock

api = mock.MagicMock()


class ConformInstances(pyblish.api.Conformer):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        uri = instance.data('assetId')

        if uri:
            # This instance has an associated entity
            # in the database, emit event
            message = "{0} was recently published".format(
                instance.data('name'))
            api.login(user='Test', password='testpass613')
            api.notify(message, uri)

            instance.set_data('notified', value=True)
