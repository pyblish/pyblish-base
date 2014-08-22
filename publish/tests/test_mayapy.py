"""Tests to be run via mayapy"""

import os

import publish.main
import publish.tests
import publish.config
import publish.domain
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

        workspace_definiton = os.path.join(self.root_path, 'workspace.mel')
        self.assertTrue(os.path.exists(workspace_definiton))

    def test_publish_all(self):
        """Publish the only instance in the scene

        The output is a single path, containing the 'model' prefix

        """

        # Todo: How do we test the success of this?
        publish.main.publish_all()

    def test_interface(self):
        """Test full interface for Publish"""

        # Parse selection
        context = publish.domain.select()
        self.assertIsInstance(context, publish.abstract.Context)

        self.assertEquals(len(context), 1)
        self.assertEqual(context.pop().name, 'publish_SEL')

        # Validate
        publish.domain.process('validators', context)
        self.assertEquals(context.errors, [])

        # Extract
        publish.domain.process('extractors', context)
        self.assertEquals(context.errors, [])

        # Conform
        # ..note:: This doesn't do anything at the moment.
        publish.domain.process('conforms', context)
        self.assertEquals(context.errors, [])

    # def test_ui_separation(self):
    #     """Getting and assigning plugins works

    #     When running Publish via a UI, we'll need to find a method of
    #     getting the plugins that will run upon each instance, and another
    #     method of assigning those plugins by hand. The UI will need to
    #     do this in order to visualise and allow users to modify them.

    #     """

    #     context = publish.domain.select()


if __name__ == '__main__':
    import unittest
    unittest.main()
