import publish.abstract
import publish.config

import maya.cmds as cmds


class SelectTransform(publish.abstract.Selector):

    def process(self):

        context = publish.domain.Context()

        for transform in cmds.ls("*." + publish.config.identifier,
                                 objectsOnly=True,
                                 type='transform'):

            instance = publish.domain.Instance(name=transform)

            instance.add(transform)

            attrs = cmds.listAttr(transform, userDefined=True)
            for attr in attrs:
                if attr == publish.config.identifier:
                    continue

                try:
                    value = cmds.getAttr(transform + "." + attr)
                except:
                    continue

                instance.config[attr] = value

            context.add(instance)

        return context
