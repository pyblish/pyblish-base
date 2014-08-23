
import publish.lib
import publish.plugin


@publish.lib.log
class ExtractInstances(publish.plugin.Extractor):
    """Extract instances"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process(self, context):
        for instance in ('inst1',):
            self.log.debug("Extracting %s" % instance)
