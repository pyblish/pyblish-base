from __future__ import absolute_import

# Standard library
import os
import time
import shutil
import logging
import tempfile

# Local library
import publish
import publish.plugin
import publish.config
import publish.abstract

log = logging.getLogger('publish')

try:
    # Running from within Maya
    from maya import mel
    from maya import cmds

except ImportError:
    from publish.mock.maya import mel
    from publish.mock.maya import cmds

    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    log.setLevel(logging.INFO)
    # log.setLevel(logging.DEBUG)


__all__ = [
    'select',
    'validate',
    'extract',
    'conform'
]


# Register plugin paths
_package_dir = os.path.dirname(publish.__file__)
_validators_path = os.path.join(_package_dir, 'validators')
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


def extract(instance):
    """Physically export data from host

    .. note:: Type of extraction depends on instance family.

    Arguments:
        instance (Instance): Instance from which to export data

    """

    assert isinstance(instance, Instance)

    family = instance.config.get('family')

    if family == 'model':
        return _extract_model(instance)

    if family == 'review':
        return _extract_review(instance)

    if family == 'pointcache':
        return _extract_pointcache(instance)

    if family == 'shader':
        return _extract_shader(instance)

    raise Warning("Unrecognised family: {0}".format(family))


def _extract_model(instance):
    """Export geometry as .mb"""

    family = instance.config.get('family')

    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'publish')

    log.info("_extract_model: Extracting locally..")
    previous_selection = cmds.ls(selection=True)
    cmds.select(list(instance), replace=True)
    cmds.file(temp_file, type='mayaBinary', exportSelected=True)

    log.info("_extract_model: Moving extraction "
             "relative working file..")
    output = _commit(temp_dir, family)

    log.info("_extract_model: Clearing local cache..")
    shutil.rmtree(temp_dir)

    if previous_selection:
        cmds.select(previous_selection, replace=True)
    else:
        cmds.select(deselect=True)

    log.info("_extract_model: Extraction successful!")
    return output


def _extract_review(instance):
    """Create playblast"""


def _extract_pointcache(instance):
    """Export alembic pointcache"""


def _extract_shader(instance):
    """Export shaders as .mb"""


def _commit(path, family):
    date = time.strftime(publish.config.dateFormat)

    workspace_dir = cmds.workspace(rootDirectory=True, query=True)
    if not workspace_dir:
        # Project has not been set. Files will
        # instead end up next to the working file.
        workspace_dir = cmds.workspace(dir=True, query=True)
    published_dir = os.path.join(workspace_dir, publish.config.prefix, family)

    commit_dir = os.path.join(published_dir, date)

    shutil.copytree(path, commit_dir)

    return commit_dir


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
        for instance in context:
            log.debug("Extracting..")
            path = extract(instance)
            log.info("Extracted {0}".format(path))

            # conform
            path = conform(path)

            paths.append(path)

            log.info("Successfully published scene")

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
import publish.maya
publish.maya.append_to_filemenu()
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
