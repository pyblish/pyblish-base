import os
import sys

import publish.abstract


class Context(publish.abstract.Context):
    """Store selected instances from currently active scene"""

    @property
    def errors(self):
        errors = list()
        for instance in self:
            errors.extend(instance.errors)
        return errors

    @property
    def has_errors(self):
        for error in self.errors:
            return True
        return False


class Instance(publish.abstract.Instance):
    """An individually publishable component within scene

    Examples include rigs, models.

    .. note:: This class isn't meant for use directly.
        See :func:context() below.

    Attributes:
        path (str): Absolute path to instance (i.e. objectSet in this case)
        config (dict): Full configuration, as recorded onto objectSet.

    """


def host():
    """Return currently active host

    When running Publish from within a host, this function determines
    which host is running and returns the equivalent keyword.

    Example:
        >> # Running within Autodesk Maya
        >> host()
        'maya'
        >> # Running within Sidefx Houdini
        >> host()
        'houdini'

    """

    if 'maya' in os.path.basename(sys.executable):
        # Maya is distinguished by looking at the currently running
        # executable of the Python interpreter. It will be something
        # like: "maya.exe" or "mayapy.exe"; without suffix for
        # posix platforms.
        return 'maya'

    else:
        raise ValueError("Could not determine host")
