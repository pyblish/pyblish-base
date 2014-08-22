"""Testing the select mechanism"""

import publish.main
import publish.tests
import publish.config
import publish.domain
import publish.abstract


class TestSelection(publish.tests.SelectTestCase):
    def test_fixture(self):
        """Fixture contains the correct nodes"""
        for node in ('Hero_AST',
                     'Villain_AST',
                     'hero_PLY',
                     'villain_PLY',
                     'Hero_AST.{id}',
                     'publish_SEL',
                     'publish_SEL.{id}'):
            node = node.format(id=publish.config.identifier)
            self.assertEquals(self.cmds.ls(node), [node])

        objectset_family = self.cmds.getAttr('publish_SEL.family')
        transform_family = self.cmds.getAttr('Hero_AST.family')
        self.assertEquals(objectset_family, 'model')
        self.assertEquals(transform_family, 'model')

    def test_select(self):
        """Selecting all items in the scene works"""
        ctx = publish.domain.Context()
        publish.domain.select(ctx)

        # There will be 2 instances in this
        # context - Hero_AST, and publish_SEL
        self.assertEquals(len(ctx), 2)

        for instance in ctx:
            name = instance.name
            assert name == 'Hero_AST' or name == 'publish_SEL'

    # def test_naming_convention(self):
    #     """The naming convention plugin is good for testing selection"""

    #     ctx = publish.domain.Context()
    #     publish.domain.select(ctx)
    #     publish.domain.process_single(
    #         'ValidateNamingConvention', ctx)

    #     self.assertEqual(len(ctx.errors), 0)
