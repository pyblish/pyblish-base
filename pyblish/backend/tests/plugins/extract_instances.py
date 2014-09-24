
import pyblish


@pyblish.log
class ExtractInstances(pyblish.Extractor):
    """Extract instances"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        self.log.debug("Extracting %s" % instance)
