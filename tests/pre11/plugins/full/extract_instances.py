
import pyblish.api


@pyblish.api.log
class ExtractInstances(pyblish.api.Extractor):
    hosts = ['python']
    families = ['full']
    version = (0, 1, 0)

    def process_instance(self, instance):
        instance.set_data('extracted', True)
