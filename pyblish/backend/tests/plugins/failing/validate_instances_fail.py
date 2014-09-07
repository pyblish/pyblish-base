
import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ValidateInstanceFail(pyblish.backend.plugin.Validator):
    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        self.log.error("Failing")
        raise ValueError("Test fail")
