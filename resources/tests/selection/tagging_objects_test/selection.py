"""Select all relevant nodes in the scene for publish"""

from maya import cmds

for objset in cmds.ls("*.publishable", objectsOnly=True):
    instances = cmds.sets(objset, query=True)
    for instance in instances:
        cls = cmds.getAttr(objset + ".class")
        print "Publishing %s for %s" % (cls, instance)

        if cls == 'pointcache':
            meshes = list()
            for child in cmds.listRelatives(instance,
                                            allDescendents=True,
                                            fullPath=True) or []:
                if not 'publishable' in (
                        cmds.listAttr(child, userDefined=True) or []):
                    continue

                try:
                    inner_cls = cmds.getAttr(child + ".class")
                except ValueError:
                    continue

                if inner_cls == 'mesh':
                    meshes.append(child)

            print "\tMeshes are: %s" % meshes

        if cls == 'animation':
            controls = list()
            for child in cmds.listRelatives(instance,
                                            allDescendents=True,
                                            fullPath=True) or []:
                if not 'publishable' in (
                        cmds.listAttr(child, userDefined=True) or []):
                    continue

                try:
                    inner_cls = cmds.getAttr(child + ".class")
                except ValueError:
                    continue

                if inner_cls == 'animation':
                    controls.append(child)

            print "\tControls are: %s" % controls
