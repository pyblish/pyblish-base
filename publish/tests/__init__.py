from __future__ import absolute_import

# Standard library
import os
# import sys
import shutil
import unittest
import tempfile

import publish
import publish.plugin

from maya import (cmds, mel, standalone)


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
        standalone.initialize(name='python')

        root_path = tempfile.mkdtemp()

        fname = 'temp.ma'

        self.mel = mel
        self.cmds = cmds
        self.fname = fname
        self.root_path = root_path

        self.create_workspace_definition()
        mel.eval('setProject "{0}"'.format(
            root_path.replace("\\", "/")))

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

        self.mel.eval(self.description)
        self.cmds.file(rename=self.fname)
        self.cmds.file(save=True, type='mayaAscii')

    def create_workspace_definition(self):
        definition = """
        //Maya 2014 Project Definition

        workspace -fr "scene" "scenes";
        workspace -fr "images" "images";
        """

        path = os.path.join(self.root_path, 'workspace.mel')
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write(definition)

    @property
    def description(self):
        return """
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


class SelectTestCase(ModelPublishTestCase):
    """Contains basic scene with two instances

    One instance is an objectSet, and the other a transform.

    """

    def setUp(self):
        super(SelectTestCase, self).setUp()
        package_dir = os.path.dirname(publish.__file__)
        validators_path = os.path.join(package_dir, 'plugins')
        validators_path = os.path.abspath(validators_path)

        publish.plugin.register_plugin_path(validators_path)

        self.nodes = (
            'Hero_AST',
            'Villain_AST',
            'hero_PLY',
            'villain_PLY',
            'publish_SEL'
        )

    @property
    def description(self):
        return """
        requires maya "2014";

        createNode transform -n "Hero_AST";
            addAttr -ci true -sn "publishable" -ln "publishable" -at "bool";
            addAttr -ci true -sn "family" -ln "family" -dt "string";
            setAttr -k on ".publishable" yes;
            setAttr -k on ".family" -type "string" "model";
        createNode transform -n "hero_PLY" -p "Hero_AST";
        createNode mesh -n "hero_PLYShape" -p "|Hero_AST|hero_PLY";
            setAttr -k off ".v";
            setAttr ".vir" yes;
            setAttr ".vif" yes;
            setAttr ".uvst[0].uvsn" -type "string" "map1";
            setAttr ".cuvs" -type "string" "map1";
            setAttr ".dcc" -type "string" "Ambient+Diffuse";
            setAttr ".covm[0]"  0 1 1;
            setAttr ".cdvm[0]"  0 1 1;
        createNode polyCube -n "polyCube1";
            setAttr ".cuv" 4;
        createNode polyCube -n "polyCube2";
            setAttr ".cuv" 4;
        createNode transform -n "Villain_AST";
        createNode transform -n "villain_PLY" -p "Villain_AST";
        createNode mesh -n "villain_PLYShape" -p "|Villain_AST|villain_PLY";
        createNode objectSet -n "publish_SEL";
            addAttr -ci true -sn "publishable" -ln "publishable" -at "bool";
            addAttr -ci true -sn "family" -ln "family" -dt "string";
            setAttr -k on ".publishable" yes;
            setAttr -k on ".family" -type "string" "model";

        connectAttr "Villain_AST.iog" "publish_SEL.dsm" -na;
        connectAttr "polyCube1.out" "|Hero_AST|hero_PLY|hero_PLYShape.i";
        connectAttr "polyCube2.out" "|Villain_AST|villain_PLY|villain_PLYShape.i";
        """
