import publish.abstract


class ValidateBlank1(publish.abstract.Validator):
    __families__ = ['animation']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
