"""Plug-in system

"""

import os
import imp
import sys


SUFFIX = "_validator.py"

validator_dirs = []


def register_plugin_path(path):
    validator_dirs.append(path)


def deregister_plugin_path(path):
    validator_dirs.remove(path)


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


def collect_validators():
    """Find and return validators

    This assumes that each test is importable within an environment.
    E.g. any host-specific imports are within function closure.

    """

    validators = dict()
    for dname in validator_dirs:
        for fname in os.listdir(dname):
            abspath = os.path.join(dname, fname)

            if not os.path.isfile(abspath):
                continue

            name, suffix = os.path.splitext(fname)

            if fname.endswith(SUFFIX):
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
    # Register validators
    module_dir = os.path.dirname(__file__)
    validators_path = os.path.join(module_dir, 'validators')

    register_plugin_path(validators_path)

    # List available validators
    for family, plugins in collect_validators().iteritems():
        print family
        for plugin in plugins:
            print "\t%s" % plugin
