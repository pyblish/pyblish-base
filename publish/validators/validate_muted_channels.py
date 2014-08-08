import publish.abstract

try:
    from maya import cmds
except ImportError:
    from publish.mock.maya import cmds


class ValidateMutedChannels(publish.abstract.Validator):
    """Ensure no muted channels exists in scene

    Todo: Ensure no muted channels are associated with involved nodes
        At the moment, the entire scene is checked.

    """

    __families__ = ['model']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        """Look for nodes of type 'mute'

        Example:
            >>> node = cmds.createNode('mute')
            >>> instance = set()
            >>> validator = ValidateMutedChannels(instance)
            >>> try:
            ...     validator.process()
            ... except ValueError:
            ...    print "Expected"
            Expected

        """

        mutes = cmds.ls(type='mute')
        if mutes:
            raise ValueError("Muted nodes found")

    def fix(self):
        mutes = cmds.ls(type='mute')
        cmds.delete(mutes)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
