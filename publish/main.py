from __future__ import absolute_import

# Standard library
import logging

# Local library
import publish.config
import publish.backend.plugin

log = logging.getLogger('publish')


__all__ = ['process',
           'select',
           'validate',
           'extract',
           'conform',
           'publish_all']


def process(process, context):
    """Perform process step `process` upon context `context`

    Arguments:
        process (str): Type of process to apply
        context (Context): Context upon which to appy process

    """

    assert isinstance(process, basestring)
    assert isinstance(context, publish.backend.plugin.Context)

    for plugin in publish.backend.plugin.discover(type=process):
        if not publish.backend.plugin.current_host() in plugin.hosts:
            continue

        log.info("Applying {process} using {plugin}".format(
            process=process,
            plugin=plugin.__name__))

        for instance, error in plugin().process(context):
            yield instance, error


def select(context):
    for instance, error in process('selectors', context):
        pass


def validate(context):
    for instance, error in process('validators', context):
        pass


def extract(context):
    for instance, error in process('extractors', context):
        pass


def conform(context):
    for instance, error in process('conforms', context):
        pass


def publish_all():
    context = publish.backend.plugin.Context()

    select(context)

    if not context:
        return log.info("No instances found")

    validate(context)
    extract(context)
    conform(context)

    return context


def validate_all():
    context = publish.backend.plugin.Context()

    select(context)
    validate(context)

    return context


if __name__ == '__main__':
    import doctest
    doctest.testmod()
