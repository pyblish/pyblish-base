"""Mockup of potential integration with 3rd-party task managment suite"""


import pyblish.backend.plugin


class ConformInstances(pyblish.backend.plugin.Conform):
    def process(self, context):
        for instance in pyblish.backend.plugin.instances_by_plugin(
                instances=context, plugin=self):
            print instance

        yield None, None
