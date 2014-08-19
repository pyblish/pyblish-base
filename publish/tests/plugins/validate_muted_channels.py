import publish.abstract

from maya import cmds


class ValidateMutedChannels(publish.abstract.Validator):
    families = ['model']
    version = (0, 1, 0)
    hosts = ['maya']

    def process(self):
        mutes = cmds.ls(type='mute')
        if mutes:
            raise ValueError("Muted nodes found")

    def fix(self):
        mutes = cmds.ls(type='mute')
        cmds.delete(mutes)
