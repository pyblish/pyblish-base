from __future__ import absolute_import

# Standard library
import os
import logging
import traceback

# Local library
import publish.plugin
import publish.config
import publish.domain

log = logging.getLogger('publish')

# Running from within Maya
from maya import mel
from maya import cmds


# Register included plugin path
_package_dir = os.path.dirname(__file__)
_validators_path = os.path.join(_package_dir, 'plugins')
_validators_path = os.path.abspath(_validators_path)
publish.plugin.register_plugin_path(_validators_path)


def select():
    """Parse currently active scene and return Context

    The context includes which nodes to extract along
    with their configuration.

    Returns:
        Context: Fully qualified context object.

    """

    plugins = publish.plugin.discover(type='selectors')

    context = publish.domain.Context()

    for plugin in plugins:

        try:
            log.info("Selecting with {plugin}".format(
                plugin=plugin.__name__))
            newContext = plugin().process()
            for instance in newContext:
                context.add(instance)
        except Exception:
            log.error(traceback.format_exc())
            log.error('An exception occured during the '
                      'execution of plugin: {0}'.format(plugin))

    return context


def process(process, context):
    """Perform process step `process` upon context `context`

    Arguments:
        process (str): Type of process to apply
        context (Context): Context upon which to appy process

    Example:
        >>> ctx = publish.domain.Context()
        >>> process('validators', ctx)
        Context([])

    """

    assert isinstance(context, publish.domain.Context)

    plugins = publish.plugin.discover(type=process)

    for instance in context:
        family = instance.config.get('family')

        log.info("Processing {inst} ({family})".format(
            inst=instance, family=family))

        # Run tests for pre-defined host and family
        for plugin in plugins:
            if not 'maya' in plugin.__hosts__:
                continue

            if not family in plugin.__families__:
                continue

            try:
                log.info("{process} {instance} with {plugin}".format(
                    process=process,
                    instance=instance,
                    plugin=plugin.__name__))
                plugin(instance).process()
            except Exception as exc:
                log.error(traceback.format_exc())
                log.error('An exception occured during the '
                          'execution of plugin: {0}'.format(plugin))
                exc.parent = instance
                exc.traceback = traceback.format_exc()
                instance.errors.append(exc)

    return context


def publish_all():
    """Convenience method of the above"""

    # parse context
    context = select()

    if not context:
        log.info("No instances found")
        return

    # Validate
    process('validators', context)

    if context.has_errors:
        log.error("There were ({n}) errors "
                  "during validation:".format(n=len(context.errors)))

        for error in context.errors:
            log.error("({n}): {error}".format(
                n=context.errors.index(error) + 1,
                error=error))
        return

    # Extract
    process('extractors', context)

    if context.has_errors:
        log.error("There were ({n}) errors "
                  "during extraction:".format(n=len(context.errors)))

        for error in context.errors:
            log.error("({n}): {error}".format(
                n=context.errors.index(error) + 1,
                error=error))


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
