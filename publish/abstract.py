
# Standard library
import abc


class Validator(object):
    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __init__(self, instance):
        self.instance = instance

    @abc.abstractmethod
    def process(self, instance):
        pass

    @abc.abstractmethod
    def fix(self, instance):
        pass


class Context(set):
    pass


class Instance(object):
    @abc.abstractproperty
    def path(self):
        pass

    @abc.abstractproperty
    def config(self):
        pass
