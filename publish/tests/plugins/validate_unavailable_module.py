import publish.abstract

import unavailable_module


class ValidateUnavailableModule(publish.abstract.Validator):
    __families__ = ['model']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
