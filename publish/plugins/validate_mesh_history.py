import publish.abstract

import pymel.core as pm


class ValidateMeshHistory(publish.abstract.Validator):
    """ Check meshes for construction history

    """

    families = ['model']
    version = (0, 1, 0)
    hosts = ['maya']

    def process(self):
        """
        """

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
