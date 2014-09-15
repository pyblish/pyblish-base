
import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ValidateOtherInstance(pyblish.backend.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.other.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        return
