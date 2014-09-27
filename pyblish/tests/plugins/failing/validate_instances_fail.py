
import pyblish.api


@pyblish.api.log
class ValidateInstanceFail(pyblish.api.Validator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        raise ValueError("Test fail")
