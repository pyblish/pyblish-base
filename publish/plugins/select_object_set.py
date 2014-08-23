import publish.lib
import publish.config
import publish.abstract

import maya.cmds as cmds


@publish.lib.log
class SelectObjectSet(publish.abstract.Selector):
    """Select instances of node-type 'transform'

    Opens up the doors for instances containing nodes of any type,
    but lacks the ability to be nested with DAG nodes.

    E.g.          -> /root/MyCharacter.publishable/an_object_set

    """

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):

        for objset in cmds.ls("*." + publish.config.identifier,
                              objectsOnly=True,
                              type='objectSet'):

            instance = publish.domain.Instance(name=objset)
            self.log.info("Adding instance: {0}".format(objset))

            for node in cmds.sets(objset, query=True):
                if cmds.nodeType(node) == 'transform':
                    descendents = cmds.listRelatives(node,
                                                     allDescendents=True)
                    for descendent in descendents:
                        instance.add(descendent)
                else:
                    instance.add(node)

            attrs = cmds.listAttr(objset, userDefined=True)
            for attr in attrs:
                if attr == publish.config.identifier:
                    continue

                try:
                    value = cmds.getAttr(objset + "." + attr)
                except:
                    continue

                # Allow name to be overriden via attribute.
                if attr == 'name':
                    instance.name = value
                    continue

                instance.config[attr] = value

            self.context.add(instance)
