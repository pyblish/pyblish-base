
# Standard library
import abc


class Filter(object):
    @abc.abstractmethod
    def process(self, instance):
        pass


class Validator(Filter):
    __families__ = []
    __hosts__ = []
    __version__ = (0, 0, 0)

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __init__(self, instance):
        self.instance = instance

    @abc.abstractmethod
    def fix(self, instance):
        pass


class Selector(Filter):
    pass


class Extractor(Filter):
    pass


class Context(set):
    pass


class Instance(set):
    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        """E.g. Instance('publish_model_SEL')"""
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __str__(self):
        """E.g. 'publish_model_SEL'"""
        return str(self.name)

    def __init__(self, name):
        super(Instance, self).__init__()
        self.name = name
        self.config = dict()
