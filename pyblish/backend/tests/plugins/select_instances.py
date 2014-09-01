
import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class SelectInstances(pyblish.backend.plugin.Selector):
    """Select instances"""

    hosts = ['python']
    version = (0, 1, 0)

    def process(self, context):
        for instance in ('inst1',):
            instance = pyblish.backend.plugin.Instance(instance)

            for node in ('node1_PLY', 'node2_PLY', 'node3_GRP'):
                instance.add(node)

            for key, value in {'publishable': True,
                               'family': 'test',
                               'startFrame': 1001,
                               'endFrame': 1025}.iteritems():

                instance.set_data(key, value)

            context.add(instance)

            yield instance, None
