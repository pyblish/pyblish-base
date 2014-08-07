import publish.abstract


class ValidateUniqueNames(publish.abstract.Validator):
    families = ['model', 'animation', 'animRig']
    version = (0, 1)
    hosts = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
