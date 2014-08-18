import publish.abstract


class ValidateBlank2(publish.abstract.Validator):
    families = ['pointcache']
    version = (0, 1, 0)
    hosts = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
