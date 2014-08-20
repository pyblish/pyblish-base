
from maya import mel
from maya import cmds


def eval_append_to_filemenu():
    """Add Publish to file-menu

    .. note:: We're going a bit hacky here, probably due to my lack
        of understanding for `evalDeferred` or `executeDeferred`,
        so if you can think of a better solution, feel free to edit.

    """

    # As Maya builds its menus dynamically upon being accessed,
    # we force its build here prior to adding our entry using it's
    # native mel function call.
    mel.eval("evalDeferred buildFileMenu")

    script = """
import publish.main

cmds.menuItem('publishOpeningDivider',
              divider=True,
              insertAfter='saveAsOptions',
              parent='mainFileMenu')
cmds.menuItem('publishScene',
              label='Publish',
              insertAfter='publishOpeningDivider',
              command=lambda _: publish.main.publish_all())
cmds.menuItem('validateScene',
              label='Validate',
              insertAfter='publishScene',
              command=lambda _: publish.main.validate_all())
cmds.menuItem('publishCloseDivider',
              divider=True,
              insertAfter='validateScene')

    """

    cmds.evalDeferred(script)


eval_append_to_filemenu()
