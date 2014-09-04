import re

import pyblish.backend.plugin


class ValidateNamingConvention(pyblish.backend.plugin.Validator):
    """Ensure each included node ends with a three-letter, upper-case type

    Example:
        clavicle_CTL <- Good
        shoulder <- Bad

    Raises:
        ValueError with an added .nodes attribute for each node
            found to be misnamed.

    """

    families = ['model', 'animation', 'animRig']
    hosts = ['maya']
    version = (0, 1, 0)

    pattern = re.compile("^\w+_\w{3}(Shape)?$")

    def process(self, context):
        """Allow nodes of appropriate names through"""

        for instance in pyblish.backend.plugin.instances_by_plugin(
                instances=context, plugin=self):
            mismatches = list()
            for node in instance:
                if not self.pattern.match(node):
                    print "Appending %s" % node
                    mismatches.append(node)

            if mismatches:
                msg = "The following nodes were misnamed\n"
                for node in mismatches:
                    msg += "\t{0}\n".format(node)

                exc = ValueError(msg)
                exc.nodes = mismatches

                yield instance, exc

            else:
                yield instance, None


if __name__ == '__main__':
    import doctest
    doctest.testmod()
