import publish.abstract

from maya import cmds


class ValidateMutedChannels(publish.abstract.Validator):
    __families__ = ['model']
    __version__ = (0, 1, 0)
    __hosts__ = ['maya']

    def process(self):
        mutes = cmds.ls(type='mute')
        if mutes:
            raise ValueError("Muted nodes found")

    def fix(self):
        mutes = cmds.ls(type='mute')
        cmds.delete(mutes)
