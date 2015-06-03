from pyblish import api


@api.log
class ValidateInstances123(api.Validator):
    hosts = ['*']
    families = ['*']
    version = (0, 0, 1)

    def process_instance(self, instance):
        raise ValueError("I was called")
