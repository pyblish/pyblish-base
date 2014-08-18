import publish.abstract

import unavailable_module


class ValidateUnavailableModule(publish.abstract.Validator):
    families = ['model']
    version = (0, 1, 0)
    hosts = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
