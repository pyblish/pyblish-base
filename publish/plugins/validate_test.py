import publish.abstract


class ValidateTest(publish.abstract.Validator):

    @property
    def families(self):
        return ['model']

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):
        print 'processing context: %s' % self.context
        for instance in self.instances:
            print 'processing instance: %s' % instance
            print 'processing nodes:'
            for node in instance:
                print node
