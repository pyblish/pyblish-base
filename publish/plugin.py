
import os
import imp
import sys


MODULE_DIR = os.path.dirname(__file__)
VALIDATOR_DIRS = [MODULE_DIR]
SUFFIX = "_validator.py"


class Validator(object):
    """Wraps plugin and forwards interface

    Usage:
        >>> validator = Validator(version=(0, 0, 1),
        ...                       hosts=['maya'],
        ...                       families=['model', 'animation'],
        ...                       plugin="module here")
        >>> validator.process()

    """

    def __str__(self):
        return self.plugin.__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __init__(self, version, hosts, families, plugin):
        self.version = version
        self.hosts = hosts
        self.families = families
        self.plugin = plugin

    def process(self):
        self.plugin.process()


def find_validators():
    """Find and return validators

    This assumes that each test is importable within an environment.
    E.g. any host-specific imports are within function closure.

    """

    validators = dict()
    for directory in VALIDATOR_DIRS:
        for root, dirs, files in os.walk(MODULE_DIR):
            for fname in files:
                name, suffix = os.path.splitext(fname)

                if fname.endswith(SUFFIX):
                    abspath = os.path.join(root, fname)
                    plugin = imp.load_source(name, abspath)

                    # Ensure valid plugin
                    if not validate_plugin(plugin):
                        sys.stderr.write(
                            "Invalid plugin: {0}".format(abspath))
                        continue

                    # Construct validator
                    families = plugin.__families__
                    hosts = plugin.__hosts__
                    version = plugin.__version__

                    validator = Validator(
                        version=version,
                        hosts=hosts,
                        families=families,
                        plugin=plugin)

                    for family in families:
                        if not family in validators:
                            validators[family] = list()

                        validators[family].append(validator)

    return validators


def validate_plugin(module):
    try:
        attrs = [
            '__families__',
            '__hosts__',
            '__version__',
            'process',
            'fix']

        for attr in attrs:
            assert attr in dir(module)

    except AssertionError:
        return False

    return True


if __name__ == '__main__':
    print find_validators()
