
import pyblish.api


@pyblish.api.log
class ValidateOtherInstance(pyblish.api.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.other.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        return
