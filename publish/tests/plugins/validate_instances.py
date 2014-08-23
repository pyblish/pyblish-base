
import re

import publish.lib
import publish.plugin


@publish.lib.log
class ValidateInstance(publish.plugin.Validator):
    """All nodes ends with a three-letter extension"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process(self, context):
        for instance in context:
            for node in instance:
                self.log.debug("Validating {0}".format(node))
                if not re.match("^\w+_\w{3}?$", node):
                    raise ValueError(
                        "{0} was named incorrectly".format(node))
