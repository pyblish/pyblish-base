
import re

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ValidateInstance(pyblish.backend.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        misnamed = list()

        for node in instance:
            self.log.debug("Validating {0}".format(node))
            if not re.match(r"^\w+_\w{3}?$", node):
                misnamed.append(node)

        if misnamed:
            raise ValueError("{0} was named incorrectly".format(node))


@pyblish.backend.lib.log
class ValidateOtherInstance(pyblish.backend.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.other.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        return
