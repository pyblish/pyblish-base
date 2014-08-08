"""Mock maya.cmds for tests

Requirements:
    1. Nodes are located in parent/child relationships
    2. Each node has attributes
    3. Each node has default attributes
    4. Each node may have user-defined attributes
    5. Each attribute has 0 or 1 connections
    6. Attributes may be nested

"""

__all__ = ['cmds',
           'mel',
           'standalone']

graph = dict()
selection = list()

default_nodes = {'defaultLightSet': 'objectSet', 'characterPartition': 'partition', 'globalCacheControl': 'globalCacheControl', 'brush1': 'brush', 'defaultRenderLayerFilter': 'objectMultiFilter', 'renderLayerFilter': 'objectMultiFilter', 'strokeGlobals': 'strokeGlobals', 'postProcessList1': 'postProcessList', 'layersFilter': 'objectMultiFilter', 'ikSystem': 'ikSystem', 'lambert1': 'lambert', 'sequenceManager1': 'sequenceManager', 'defaultRenderQuality': 'renderQuality', 'defaultRenderingList1': 'defaultRenderingList', 'defaultRenderGlobals': 'renderGlobals', 'defaultResolution': 'resolution', 'topShape': 'camera', 'defaultTextureList1': 'defaultTextureList', 'initialShadingGroup': 'shadingEngine', 'perspShape': 'camera', 'top': 'transform', 'initialMaterialInfo': 'materialInfo', 'time1': 'time', 'objectTypeFilter81': 'objectTypeFilter', 'objectTypeFilter80': 'objectTypeFilter', 'renderingSetsFilter': 'objectMultiFilter', 'objectTypeFilter76': 'objectTypeFilter', 'defaultObjectSet': 'objectSet', 'renderGlobalsList1': 'renderGlobalsList', 'dof1': 'dof', 'objectTypeFilter77': 'objectTypeFilter', 'dynController1': 'dynController', 'renderLayerManager': 'renderLayerManager', 'defaultViewColorManager': 'viewColorManager', 'lightList1': 'lightList', 'hardwareRenderGlobals': 'hardwareRenderGlobals', 'CustomGPUCacheFilter': 'objectMultiFilter', 'hyperGraphLayout': 'hyperLayout', 'renderPartition': 'partition', 'defaultLightList1': 'defaultLightList', 'particleCloud1': 'particleCloud', 'hyperGraphInfo': 'hyperGraphInfo', 'objectScriptFilter10': 'objectScriptFilter', 'animLayersFilter': 'objectMultiFilter', 'defaultRenderLayer': 'renderLayer', 'defaultLayer': 'displayLayer', 'front': 'transform', 'relationshipPanel1RightAttrFilter': 'objectMultiFilter', 'lightLinker1': 'lightLinker', 'defaultRenderUtilityList1': 'defaultRenderUtilityList', 'objectTypeFilter78': 'objectTypeFilter', 'shaderGlow1': 'shaderGlow', 'notAnimLayersFilter': 'objectMultiFilter', 'objectTypeFilter79': 'objectTypeFilter', 'persp': 'transform', 'initialParticleSE': 'shadingEngine', 'defaultHardwareRenderGlobals': 'hwRenderGlobals', 'side': 'transform', 'layerManager': 'displayLayerManager', 'objectNameFilter4': 'objectNameFilter', 'relationshipPanel1LeftAttrFilter': 'objectMultiFilter', 'defaultShaderList1': 'defaultShaderList', 'hardwareRenderingGlobals': 'hardwareRenderingGlobals', 'frontShape': 'camera', 'sideShape': 'camera'}


class MockNode(object):
    """Emulate DG-node"""

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"%s(%r)" % (type(self).__name__, self.__str__())

    def __getattr__(self, attr):
        return self.attributes.get(attr)

    def __init__(self, name, type, parent=None):
        self.type = type
        self.name = name
        self.parent = parent
        self.children = list()
        self.attributes = dict()

        if parent:
            parent.add_child(self)

    def add_child(self, child):
        self.children.append(child)

    def add_attribute(self, key, value):
        if not isinstance(value, MockAttribute):
            value = MockAttribute(value)
        self.attributes[key] = value


class MockAttribute(object):
    """Emulate DG-node attribute"""
    def __init__(self, name, parent=None):
        self.name = name
        self.connected_to = list()

    def connect(self, node):
        assert isinstance(node, MockNode)


class AbstractMock(object):
    def __getattr__(self, attr):
        return self.mock_function

    @staticmethod
    def mock_function(attr, *args, **kwargs):
        return None


class Standalone(AbstractMock):
    pass


class Cmds(AbstractMock):
    def ls(self, *objs, **kwargs):
        """Mock of maya.cmds.ls

        Example:
            >>> cmds.ls('defaultLightSet')
            ['defaultLightSet']

        """

        matches = list()

        if not objs:
            return graph.keys()

        for obj in objs:
            if obj in graph:
                matches.append(obj)

        return matches

    def createNode(self, type, *args, **kwargs):
        """Mock of maya.cmds.createNode

        Example:
            >>> node = cmds.createNode('mesh', name='MyNode')
            >>> assert node == 'MyNode'

        """

        interface = ['name', 'parent', 'shared', 'skipSelect']
        args = list(args)
        index = 0

        while args:
            try:
                arg = args.pop(0)
                kwargs[interface[index]] = arg
                index += 1
            except IndexError:
                raise ValueError("Too many positional arguments")

        name = kwargs.get('name') or "{}1".format(type)
        node = MockNode(name, type)
        graph[name] = node

        return name

    def nodeType(self, name):
        """Mock of maya.cmds.nodeType

        Example:
            >>> node = cmds.createNode('mesh')
            >>> assert cmds.nodeType(node) == 'mesh'

        """

        try:
            node = graph[name]
        except KeyError:
            raise RuntimeError("No object matches name: {0}".format(name))

        return node.type


class Mel(AbstractMock):
    pass


def initialise():
    """Populate graph with default nodes"""
    for node, type in default_nodes.iteritems():
        graph[node] = MockNode(node, type)


initialise()
cmds = Cmds()
mel = Mel()
standalone = Standalone()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    node = cmds.createNode('mesh', name='MyNode')
    print cmds.ls('MyNode')
