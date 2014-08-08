import publish.abstract


class ValidateUniqueNames(publish.abstract.Validator):
    __families__ = ['model', 'animation', 'animRig']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
