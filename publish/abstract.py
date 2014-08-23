
# Standard library
import abc


class Filter(object):
    """Abstract base-class for sequential plugins

    Sequential plugins are those that takes as input what it gives
    as output and may thus be arranged in any arbitrary order.

    E.g. Validators are filters. Validators may get executed in any
    order whilst still producing identical results. The same goes
    for Extractors.

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def families(self):
        """Return list of supported families, e.g. 'model'"""
        return list()

    @abc.abstractproperty
    def hosts(self):
        """Return list of supported hosts, e.g. 'maya'"""
        return list()

    @abc.abstractproperty
    def version(self):
        """Return tuple of version, e.g. (1, 3, 14)"""
        return (0, 0, 0)

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __init__(self, instance):
        self.instance = instance
        self.errors = list()

    @abc.abstractmethod
    def process(self):
        return None


class Selector(object):
    """Parse a given working scene for available Instances.

    Selectors operate on the context and injects it with
    discovered Instances.

    Attributes:
        hosts (list): List of strings for supported hosts e.g. Maya

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def hosts(self):
        return list()

    @abc.abstractproperty
    def version(self):
        return tuple()

    def __init__(self, context):
        self.context = context

    @abc.abstractmethod
    def process(self):
        return None


class Validator(Filter):
    """Validate/check/test individual instance for correctness.

    It either raises an exception, which are caught by the erroring instance,
    or does nothing; indicating success.

    """

    def fix(self):
        """Optional auto-fix for when validation fails"""


class Extractor(Filter):
    """Physically separate Instance from Host into corresponding Resources

    An extractor operats on Instances and its content to produce
    the corresponding files on disk.

    """


class Context(set):
    """Maintain a collection of Instances"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def errors(self):
        """Return errors occured in contained instances"""

    @abc.abstractproperty
    def has_errors(self):
        """Return True if Context contains errors, False otherwise"""


class Instance(set):
    """Maintain a collection of nodes along with their configuration"""

    def __hash__(self):
        """Instances are distinguished solely by their name

        This is in contrast to Python sets in general which are mutable
        and can thus not be part of another collection, such as lists
        or other sets. Since we're collecting Instances within Context
        they must be collectible and identifying them by name seems
        appropriate.

        """

        return hash(self.name)

    def __repr__(self):
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __str__(self):
        return str(self.name)

    def __init__(self, name):
        super(Instance, self).__init__()
        self.name = name
        self.config = dict()
        self.errors = list()
