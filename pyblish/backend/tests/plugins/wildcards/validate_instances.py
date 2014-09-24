from pyblish import api


@api.log
class ValidateInstances(api.Validator):
    hosts = ['*']
    families = ['*']
    version = (0, 0, 1)

    def process_instance(self, context):
        raise ValueError("I was called")
