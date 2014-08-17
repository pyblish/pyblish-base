import publish.abstract
import publish.config

import maya.cmds as cmds


class SelectObjectSet(publish.abstract.Selector):

    def process(self):

        context = publish.domain.Context()

        for objset in cmds.ls("*." + publish.config.identifier,
                              objectsOnly=True,
                              type='objectSet'):

            instance = publish.domain.Instance(name=objset)

            for node in cmds.sets(objset, query=True):
                instance.add(node)

            attrs = cmds.listAttr(objset, userDefined=True)
            for attr in attrs:
                if attr == publish.config.identifier:
                    continue

                try:
                    value = cmds.getAttr(objset + "." + attr)
                except:
                    continue

                instance.config[attr] = value

            context.add(instance)

        return context
