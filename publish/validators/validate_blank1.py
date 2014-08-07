import publish.abstract


class ValidateBlank1(publish.abstract.Validator):
    families = ['animation']
    version = (0, 1)
    hosts = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
