"""Tests to be run via mayapy"""

import publish.main
import publish.tests
import publish.config
import publish.abstract


class TestMayaPy(publish.tests.ModelPublishTestCase):
    def test_fixture(self):
        """Fixture contains these elements"""

        for node in ('body_GEO',
                     'publish_SEL',
                     'publish_SEL.{id}'.format(
                         id=publish.config.identifier)):
            self.assertTrue(self.cmds.objExists(node))

        self.assertEquals(self.cmds.getAttr('publish_SEL.family'),
                          'model')

    def test_publish_all(self):
        """Publish the only instance in the scene

        The output is a single path, containing the 'model' prefix

        """

        publish.main.publish_all()

    def test_interface(self):
        """Test full interface for Publish"""

        # Parse selection
        context = publish.main.select()
        self.assertIsInstance(context, publish.abstract.Context)

        # Validate
        publish.main.process('validators', context)
        self.assertEquals(context.errors, [])

        # Extract
        publish.main.process('extractors', context)
        self.assertEquals(context.errors, [])

        # Conform
        # ..note:: This doesn't do anything at the moment.
        publish.main.process('conforms', context)
        self.assertEquals(context.errors, [])


if __name__ == '__main__':
    import unittest
    unittest.main()
