import publish.abstract


class ValidateUniqueNames(publish.abstract.Validator):

    @property
    def families(self):
        return ['model', 'animation', 'animRig']

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):
        pass

    def fix(self):
        pass
