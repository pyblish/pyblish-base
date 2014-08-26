
import publish.lib
import publish.backend.plugin


@publish.lib.log
class ExtractInstances(publish.backend.plugin.Extractor):
    """Extract instances"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process(self, context):
        instances = list()

        for name in ('inst1', 'inst2'):
            instances.append(publish.backend.plugin.Instance(name))

        for instance in instances:
            self.log.debug("Extracting %s" % instance)

            yield instance, None


@publish.lib.log
class ExtractInstancesFail(publish.backend.plugin.Extractor):
    """Extract instances"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process(self, context):
        for instance in ('inst1',):
            yield instance, ValueError(
                "Could not extract {0}".format(instance))
