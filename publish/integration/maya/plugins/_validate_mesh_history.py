import publish.plugin

import pymel.core as pm


class ValidateMeshHistory(publish.plugin.Validator):
    """Check meshes for construction history"""

    @property
    def families(self):
        return ['model']

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):
        for node in self.instance:
            node = pm.PyNode(node)
            if node.inMesh.listConnections():
                exc = ValueError('Construction History on: %s' % node)
                raise exc

    def fix(self):
        for node in self.instance:
            node = pm.PyNode(node)
            pm.delete(node, ch=True)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
