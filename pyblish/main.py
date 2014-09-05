"""Entry-point of Pyblish"""

from __future__ import absolute_import

# Standard library
import logging

# Local library
import pyblish.backend.config
import pyblish.backend.plugin

log = logging.getLogger('pyblish.main')


__all__ = ['process',
           'select',
           'validate',
           'extract',
           'conform',
           'publish_all']


def process(type, context):
    """Perform process `type` upon context `context`

    Arguments:
        type (str): Type of process to apply
        context (Context): Context upon which to appy process

    """

    assert isinstance(type, basestring)
    assert isinstance(context, pyblish.backend.plugin.Context)

    for plugin in pyblish.backend.plugin.discover(type=type):
        current_host = pyblish.backend.plugin.current_host()
        if not '*' in plugin.hosts and not current_host in plugin.hosts:
            continue

        for instance, error in plugin().process(context):
            log.info("Running {process} with {plugin} on {subject}".format(
                process=type,
                plugin=plugin,
                subject=getattr(instance, 'name', context)))
            yield instance, error


def process_all(type, context):
    """Convenience function of the above :meth:process"""
    for instance, error in process(type, context):
        if error is not None:
            raise error


def select(context):
    """Convenience function for selecting using all available plugins"""
    try:
        process_all('selectors', context)
    except Exception as error:
        log.error(error)


def validate(context):
    """Convenience function for validation"""
    process_all('validators', context)


def extract(context):
    """Convenience function for extraction"""
    try:
        process_all('extractors', context)
    except Exception as error:
        log.error(error)


def conform(context):
    """Perform conform upon context `context`"""
    try:
        process_all('conforms', context)
    except Exception as error:
        log.error(error)


def publish_all(context=None):
    """Convenience method for executing all steps in sequence

    Arguments:
        context (Context): Optional context

    """

    log.info("Publishing everything..")

    if not context:
        context = pyblish.backend.plugin.Context()

    select(context)

    if not context:
        return log.info("No instances found.")

    validate(context)  # Will raise exception at failure
    extract(context)
    conform(context)

    log.info("Finished successfully")

    return context


def validate_all(context=None):
    if not context:
        context = pyblish.backend.plugin.Context()

    select(context)
    validate(context)

    log.info("All instances valid")
