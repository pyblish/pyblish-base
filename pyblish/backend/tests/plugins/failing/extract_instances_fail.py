
import pyblish


@pyblish.log
class ExtractInstancesFail(pyblish.Extractor):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        raise ValueError("Could not extract {0}".format(instance))
