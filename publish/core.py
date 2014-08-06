

# Base Classes
# ============
class Context(object):
    pass


class Action(object):
    """ Action that operates on a predefined Context.
        An action will have to define what type of Context it requires as well as
        what data on such Context it uses. This way we can raise errors when one of
        the dependencies is not met with a certain Context.

        `__inputs__` refers to what data this Action requires to already exist on the Context
        `__outputs__` refers to what data this Action will add/edit on the Context
    """
    __context__ = Context   # The type of Context the action operates on
    __inputs__ = None
    __outputs__ = None

    def __init__(self, context=None):
        self.__context = None

        if context is not None:
            self.context = context

    @context.setter
    def context(self, c):
        assert isinstance(c, self.__context__)
        self.__context = c

    @property
    def context(self):
        return self.__context


# The different types of default Action that operate on a Context: Selector, Validator, Extractor
class Selector(Action):
    def process(self, context=None):
        if context is None:
            context = self.__context__() # Instantiate an empty Context if None provided
        raise NotImplementedError("Must be implemented in child class")


class Validator(Action):
    def process(self, context):
        raise NotImplementedError("Must be implemented in child class")


class Extractor(Action):
    def process(self):
        raise NotImplementedError("Must be implemented in child class")
