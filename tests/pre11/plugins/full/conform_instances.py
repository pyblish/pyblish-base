
import pyblish.api


@pyblish.api.log
class ConformInstances(pyblish.api.Conformer):
    hosts = ['python']
    families = ['full']
    version = (0, 1, 0)

    def process_instance(self, instance):
        instance.set_data('conformed', True)
