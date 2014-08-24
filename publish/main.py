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

    print "Processing ctx: %s with %s" % (context, process)

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
    return process('selectors', context)


def validate(context):
    return process('validators', context)


def extract(context):
    return process('extractors', context)


def conform(context):
    return process('conforms', context)


def publish_all():
    context = publish.backend.plugin.Context()

    for instance, error in select(context):
        print "Selected {0}".format(instance)

    if not context:
        return log.info("No instances found")

    for p in (validate, extract, conform):
        for instance, error in p(context):
            print "{process} {inst}".format(process=p, inst=instance)
            if error:
                print error

        print "Process: %s" % p

    print "Finished"
    return context


def validate_all():
    context = publish.backend.plugin.Context()

    select(context)
    validate(context)

    return context


if __name__ == '__main__':
    import doctest
    doctest.testmod()
