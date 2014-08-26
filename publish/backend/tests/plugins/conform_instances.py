"""Mockup of potential integration with 3rd-party task managment suite"""


import publish.backend.plugin


class ConformInstances(publish.backend.plugin.Conform):
    def process(self, context):
        for instance in publish.backend.plugin.instances_by_plugin(
                instances=context, plugin=self):
            print instance

        yield None, None
