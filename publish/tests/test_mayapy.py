"""Tests to be run via mayapy"""

import os
import json

import publish
import publish.maya
import publish.tests
import publish.abstract


class TestMayaPy(publish.tests.ModelPublishTestCase):
    def test_fixture(self):
        """Fixture contains these elements"""

        for node in ('body_GEO',
                     'publish_SEL',
                     'publish_SEL.{id}'.format(
                         id=publish.maya.config['identifier'])):
            self.assertTrue(self.cmds.objExists(node))

        self.assertEquals(self.cmds.getAttr('publish_SEL.family'),
                          'model')

    def test_publish_all(self):
        """Publish the only instance in the scene

        The output is a single path, containing the 'model' prefix

        """

        path = publish.maya.publish_all()[0]
        path = os.path.normpath(path)
        expected_path = os.path.join(self.root_path,
                                     publish.maya.config['prefix'],
                                     'model')
        self.assertIn(expected_path, path)

    def test_interface(self):
        """Test full interface for Publish"""

        # parse selection
        context = publish.maya.select()
        self.assertIsInstance(context, publish.abstract.Context)

        # validate
        failures = publish.maya.validate(context)
        self.assertEquals(failures, [])

        # extract
        instance = context.pop()
        path = publish.maya.extract(instance)
        path = os.path.normpath(path)
        expected_path = os.path.join(self.root_path,
                                     publish.maya.config['prefix'],
                                     'model')
        self.assertIn(expected_path, path)

        # Conform isn't doing anything currently
        self.assertEquals(publish.maya.conform(path), path)

    def test_persistent_configuration(self):
        """Configuration is stored directly within the package"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        self.assertEquals(config, publish.maya.config)


if __name__ == '__main__':
    import unittest
    unittest.main()
