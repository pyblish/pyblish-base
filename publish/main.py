from __future__ import absolute_import

# Standard library
import logging

# Local library
import publish.plugin
import publish.config

log = logging.getLogger('publish')


def process(process, context):
    """Perform process step `process` upon context `context`

    Arguments:
        process (str): Type of process to apply
        context (Context): Context upon which to appy process

    Example:
        >>> import publish.plugin
        >>> ctx = publish.plugin.Context()
        >>> inst = publish.plugin.Instance('MyInstance')
        >>> inst.add('MyItem')
        >>> ctx.add(inst)
        >>> process('validators', ctx)
        Context([Instance('MyInstance')])

    """

    assert isinstance(process, basestring)
    assert isinstance(context, publish.plugin.Context)

    for plugin in publish.plugin.discover(type=process):
        if not publish.plugin.current_host() in plugin.hosts:
            continue

        log.info("Applying {process} using {plugin}".format(
            process=process,
            plugin=plugin.__name__))
        plugin().process(context)

    return context


def select(context):
    return process(context, 'selectors')


def validate(context):
    return process(context, 'validators')


def extract(context):
    return process(context, 'extractors')


def conform(context):
    return process(context, 'conforms')


def publish_all():
    context = publish.plugin.Context()

    select(context)
    validate(context)
    extract(context)
    conform(context)

    return context


def validate_all():
    context = publish.plugin.Context()

    select(context)
    validate(context)

    return context


if __name__ == '__main__':
    import doctest
    doctest.testmod()
