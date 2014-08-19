from __future__ import absolute_import

# Standard library
import logging
import traceback

# Local library
import publish.plugin
import publish.config
import publish.domain

log = logging.getLogger('publish')


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
        if not publish.domain.host() in plugin.hosts:
            continue

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
            if not publish.domain.host() in plugin.hosts:
                continue

            if not family in plugin.families:
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
