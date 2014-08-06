"""Test for unique names within a Maya scene

Attributes:
    __families__: In which families this test applies.
    __version__: Current version
    __hosts__: Supported hosts

"""

__families__ = ['model', 'animation', 'animRig']
__version__ = (0, 1)
__hosts__ = ['maya']


def process(context):
    """Test scene for unique names

    Arguments:
        context: Current context for validator

    Raises:
        Exception if any unique names are found.

    """

    from maya import cmds

    names = list()
    for name in cmds.ls():
        if name in names:
            raise ValueError("Duplicate name: %s" % name)
        names.append(name)


def fix(context):
    """Attempt to resolve duplicate names"""
