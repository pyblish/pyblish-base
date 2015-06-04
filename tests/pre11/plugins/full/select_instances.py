
import pyblish.api


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    hosts = ['python']
    version = (0, 1, 0)

    def process_context(self, context):
        inst = context.create_instance(name='Test')
        inst.set_data('family', 'full')
        inst.set_data('selected', True)

        # The following will be set during
        # processing of other plugins
        inst.set_data('validated', False)
        inst.set_data('extracted', False)
        inst.set_data('conformed', False)
