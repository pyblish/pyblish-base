
import pyblish.api


@pyblish.api.log
class ValidateInstance(pyblish.api.Validator):
    hosts = ['python']
    families = ['full']
    version = (0, 1, 0)

    def process_instance(self, instance):
        instance.set_data('validated', True)
