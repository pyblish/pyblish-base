import publish.abstract
import publish.config

import maya.cmds as cmds


class SelectTransform(publish.abstract.Selector):
    """Select instances of node-type 'transform'

    Opens up the doors for nested instances.

    E.g.          -> /root/characters_GRP/MyCharacter.publishable
    As opposed to -> /root/MyCharacter.publishable

    But lacks ability to append non-DAG nodes.

    E.g.          -> /root/MyCharacter.publishable/an_object_set

    """

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):
        for transform in cmds.ls("*." + publish.config.identifier,
                                 objectsOnly=True,
                                 type='transform'):

            instance = publish.domain.Instance(name=transform)

            instance.add(transform)
            for child in cmds.listRelatives(transform, allDescendents=True):
                    instance.add(child)

            attrs = cmds.listAttr(transform, userDefined=True)
            for attr in attrs:
                if attr == publish.config.identifier:
                    continue

                try:
                    value = cmds.getAttr(transform + "." + attr)
                except:
                    continue

                instance.config[attr] = value

            self.context.add(instance)

        return self.context
