
import re

import publish.lib
import publish.backend.plugin


@publish.lib.log
class ValidateInstance(publish.backend.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process(self, context):
        for instance in context:
            misnamed = list()

            for node in instance:
                self.log.debug("Validating {0}".format(node))
                if not re.match("^\w+_\w{3}?$", node):
                    misnamed.append(node)

            if misnamed:
                yield instance, ValueError(
                    "{0} was named incorrectly".format(node))
            else:
                yield instance, None


@publish.lib.log
class ValidateOtherInstance(publish.backend.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.other.family']
    version = (0, 1, 0)

    def process(self, context):
        yield None, None
