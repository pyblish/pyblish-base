import publish.abstract


class ValidateMutedChannels(publish.abstract.Validator):
    families = ['model']
    version = (0, 1)
    hosts = ['maya']

    def process(self):
        pass

    def fix(self):
        pass
