from __future__ import absolute_import

# Standard library
import os
import logging

# Local library
import publish.plugin
import publish.config
import publish.abstract

log = logging.getLogger('publish')

# Running from within Maya
from maya import mel
from maya import cmds

__all__ = [
    'select',
    'validate',
    'extract',
    'conform',
    'publish_all'
]


# Register included plugin path
_package_dir = os.path.dirname(__file__)
_validators_path = os.path.join(_package_dir, 'plugins')
_validators_path = os.path.abspath(_validators_path)
publish.plugin.register_plugin_path(_validators_path)


class Context(publish.abstract.Context):
    """Store selected instances from currently active scene"""


class Instance(publish.abstract.Instance):
    """An individually publishable component within scene

    Examples include rigs, models.

    .. note:: This class isn't meant for use directly.
        See :func:context() below.

    Attributes:
        path (str): Absolute path to instance (i.e. objectSet in this case)
        config (dict): Full configuration, as recorded onto objectSet.

    """


def select():
    """Parse currently active scene and return context object.

    The context includes which nodes to extract along
    with their configuration.

    Returns:
        Context: Fully qualified context object.

    """

    context = Context()

    for objset in cmds.ls("*." + publish.config.identifier,
                          objectsOnly=True,
                          type='objectSet'):

        instance = Instance(name=objset)

        for node in cmds.sets(objset, query=True):
            instance.add(node)

        attrs = cmds.listAttr(objset, userDefined=True)
        for attr in attrs:
            if attr == publish.config.identifier:
                continue

            try:
                value = cmds.getAttr(objset + "." + attr)
            except:
                continue

            instance.config[attr] = value

        context.add(instance)

    return context


def validate(context):
    """Validate context `context`

    Arguments:
        context (Context): Parsed context

    Returns:
        True is successful, False otherwise

    """

    assert isinstance(context, Context)

    plugins = publish.plugin.discover(type='validators')

    errors = list()

    for instance in context:
        family = instance.config.get('family')

        # Run tests for pre-defined host and family
        for Validator in plugins:
            if not 'maya' in Validator.__hosts__:
                continue

            if not family in Validator.__families__:
                continue

            try:
                log.info("Validating {instance} with {plugin}".format(
                    instance=instance, plugin=Validator.__name__))
                Validator(instance).process()
            except Exception as exc:
                errors.append(exc)

    return errors


def extract(context):
    assert isinstance(context, Context)

    plugins = publish.plugin.discover(type='extractors')

    errors = list()

    for instance in context:
        family = instance.config.get('family')

        # Run tests for pre-defined host and family
        for Validator in plugins:
            if not 'maya' in Validator.__hosts__:
                continue

            if not family in Validator.__families__:
                continue

            try:
                log.info("Extracting {instance} with {plugin}".format(
                    instance=instance, plugin=Validator.__name__))
                Validator(instance).process()
            except Exception as exc:
                errors.append(exc)

    return errors


def conform(path):
    log.info("Moving %s to new home" % path)
    return path


def publish_all():
    """Convenience method of the above"""

    # parse context
    log.debug("Selecting..")
    context = select()

    if not context:
        log.info("No instances found")
        return

    # validate
    log.debug("Validating..")
    errors = validate(context)

    # extract
    paths = list()
    if not errors:
        log.debug("Extracting..")
        extract(context)
        conform(context)

    else:
        log.error("There were ({n}) errors:".format(n=len(errors)))
        for error in errors:
            log.error("({n}): {error}".format(n=errors.index(error) + 1,
                                              error=error))

    return paths


def append_to_filemenu():
    """Add Publish to file-menu

    As Maya builds its menus upon first being accessed,
    you'll have to use eval_append_to_filemenu() below
    if triggered automatically at startup; such as in
    your userSetup.py

    """

    cmds.menuItem('publishOpeningDivider',
                  divider=True,
                  insertAfter='saveAsOptions',
                  parent='mainFileMenu')
    cmds.menuItem('publishScene',
                  label='Publish',
                  insertAfter='publishOpeningDivider',
                  command=lambda _: publish_all())
    cmds.menuItem('publishCloseDivider',
                  divider=True,
                  insertAfter='publishScene')
    log.info("Success")


def eval_append_to_filemenu():
    """Add Publish to file-menu"""
    mel.eval("evalDeferred buildFileMenu")

    script = """
import publish.main
publish.main.append_to_filemenu()
    """

    cmds.evalDeferred(script)


if __name__ == '__main__':
    import publish.plugin

    # Register validators
    module_dir = os.path.dirname(__file__)
    validators_path = os.path.join(module_dir, 'validators')

    publish.plugin.register_plugin_path(validators_path)

    # List available validators
    for plugin in publish.plugin.discover('validators'):
        print "%s" % plugin
