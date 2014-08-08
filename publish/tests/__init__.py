
# Standard library
import os
import sys
import shutil
import unittest
import tempfile

import publish
import publish.plugin


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Include basic validations"""

        publish.plugin.deregister_all()

        package_dir = os.path.dirname(publish.__file__)
        validators_path = os.path.join(package_dir, 'tests', 'plugins')
        validators_path = os.path.abspath(validators_path)

        publish.plugin.register_plugin_path(validators_path)

        config_path = os.path.join(package_dir, 'config.json')

        self.config_path = config_path
        self.validators_path = validators_path

    def tearDown(self):
        publish.plugin.deregister_plugin_path(self.validators_path)


class ModelPublishTestCase(BaseTestCase):
    """Baseclass for tests using a plain scene with one publishable instance"""

    def setUp(self):
        """Construct simple Maya scene"""
        super(ModelPublishTestCase, self).setUp()

        if not "maya" in sys.executable.lower():
            raise Warning("This should only be run from within mayapy")

        from maya import cmds
        from maya import mel
        from maya import standalone

        standalone.initialize(name='python')

        root_path = tempfile.mkdtemp()
        mel.eval('setProject "{0}"'.format(
            root_path.replace("\\", "/")))

        fname = 'temp.ma'

        self.mel = mel
        self.cmds = cmds
        self.fname = fname
        self.root_path = root_path

        self.create_scene()

    def tearDown(self):
        super(ModelPublishTestCase, self).tearDown()

        shutil.rmtree(self.root_path)
        self.cmds.file(new=True)

    def create_scene(self):
        """Create basic scene

        body_GEO
        publish_SEL/
            .publishable=True
            .family="model"
            body_GEO

        """

        description = """
        //Maya ASCII 2014 scene
        //Name: test.ma
        requires maya "2014";
        createNode transform -n "body_GEO";
        createNode mesh -n "body_GEOShape" -p "body_GEO";
        createNode objectSet -n "publish_SEL";
            addAttr -sn "publishable" -ln "publishable" -at "bool";
            addAttr -sn "family" -ln "family" -dt "string";
            setAttr ".ihi" 0;
            setAttr -k on ".publishable" yes;
            setAttr -k on ".family" -type "string" "model";
        createNode polyCube -n "polyCube1";
        connectAttr "polyCube1.out" "body_GEOShape.i";
        connectAttr "body_GEO.iog" "publish_SEL.dsm" -na;
        // End of test.ma
        """

        self.mel.eval(description)
        self.cmds.file(rename=self.fname)
        self.cmds.file(save=True, type='mayaAscii')
