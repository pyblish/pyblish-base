
import pyblish.api


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    """Select instances"""

    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        instance = context.create_instance(name='inst1')

        for node in ('node1_PLY', 'node2_PLY', 'node3_GRP'):
            instance.add(node)

        for key, value in {
                'publishable': True,
                'family': 'test',
                'startFrame': 1001,
                'endFrame': 1025
                }.iteritems():

            instance.set_data(key, value)

        context.add(instance)

        return
