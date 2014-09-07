"""Validate naming convention (Demo)"""

import re

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ValidateNamingConvention(pyblish.backend.plugin.Validator):
    """Ensure each included node ends with a three-letter, upper-case type

    Example:
        clavicle_CTL <- Good
        shoulder <- Bad

    Raises:
        ValueError with an added .nodes attribute for each node
            found to be misnamed.

    """

    families = ['demo.model']
    hosts = ['*']
    version = (0, 1, 1)

    # Naming convention to test for
    pattern = re.compile("^\w+_\w{3}(Shape)?$")

    def process_instance(self, instance):
        """Allow nodes of appropriate names through"""
        mismatches = list()
        for node in instance:
            if not self.pattern.match(node):
                self.log.debug("Misnamed: {0}".format(node))
                mismatches.append(node)

        if mismatches:
            msg = "The following nodes were misnamed\n"
            for node in mismatches:
                msg += "\t{0}\n".format(node)

            err = ValueError(msg)
            err.nodes = mismatches

            raise err
