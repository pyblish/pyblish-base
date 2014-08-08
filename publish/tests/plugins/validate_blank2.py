import publish.abstract


class ValidateBlank2(publish.abstract.Validator):
    __families__ = ['pointcache']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
