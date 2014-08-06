"""Test for the existence of muted channels

Attributes:
    __families__: In which families this test applies.
    __version__: Current version
    __hosts__: Supported hosts

"""

__families__ = ['model']
__version__ = (0, 1)
__hosts__ = ['maya']


def process(context):
    """Test scene for muted channels

    Raises:
        Exception if any unique names are found.

    """

    from maya import cmds

    muted_channels = cmds.ls(type='mute')
    if muted_channels:
        raise ValueError("Muted channels exist: {0}".format(muted_channels))


def fix(context):
    """Attempt to resolve muted channels"""

    from maya import cmds

    muted_channels = cmds.ls(type='mute')
    try:
        cmds.delete(muted_channels)
    except:
        raise
