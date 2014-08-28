"""Entry-point of Pyblish"""

from __future__ import absolute_import

# Standard library
import logging

# Local library
import pyblish.backend.config
import pyblish.backend.plugin

log = logging.getLogger('pyblish')


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
    assert isinstance(context, pyblish.backend.plugin.Context)

    for plugin in pyblish.backend.plugin.discover(type=process):
        if not pyblish.backend.plugin.current_host() in plugin.hosts:
            continue

        log.info("Applying {process} using {plugin}".format(
            process=process,
            plugin=plugin.__name__))

        for instance, error in plugin().process(context):
            yield instance, error


def select(context):
    """Perform selection upon context `context`"""
    return process('selectors', context)


def validate(context):
    """Perform validation upon context `context`"""
    return process('validators', context)


def extract(context):
    """Perform extraction upon context `context`"""
    return process('extractors', context)


def conform(context):
    """Perform conform upon context `context`"""
    return process('conforms', context)


def publish_all():
    """Convenience method for executing all steps in sequence"""
    context = pyblish.backend.plugin.Context()

    for instance, error in select(context):
        print "Selected {0}".format(instance)

    if not context:
        return log.info("No instances found")

    for instance, error in validate(context):
        if error is not None:
            # Stop immediately if any validation fails
            raise error

    for p in (extract, conform):
        for instance, error in p(context):
            print "{process} {inst}".format(process=p, inst=instance)
            if error is not None:
                # Continue regardless
                print error

        print "Process: %s" % p

    print "Finished"
    return context


def validate_all():
    context = pyblish.backend.plugin.Context()

    for instance, error in select(context):
        pass

    for instance, error in validate(context):
        if error is not None:
            raise error

    return context


if __name__ == '__main__':
    import doctest
    doctest.testmod()
