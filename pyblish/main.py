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
    """Perform process step `process` upon context `context`

    Arguments:
        process (str): Type of process to apply
        context (Context): Context upon which to appy process

    """

    assert isinstance(type, basestring)
    assert isinstance(context, pyblish.backend.plugin.Context)

    host = pyblish.backend.plugin.current_host()
    plugins = pyblish.backend.plugin.discover(type=type)
    compatible_plugins = pyblish.backend.plugin.plugins_by_host(plugins, host)

    for plugin in compatible_plugins:
        for instance, error in plugin().process(context):
            yield instance, error


def process_all(type, context):
    """Convenience function of the above :meth:process

    .. note:: Keep in mind that this won't continue if
        there an error occurs.

    """

    for instance, error in process(type, context):
        if error is not None:
            raise error


def select(context):
    """Convenience function for selecting using all available plugins"""
    for instance, error in process('selectors', context):
        if error is not None:
            log.error(error)


def validate(context):
    """Convenience function for validation"""
    processed = list()

    for instance, error in process('validators', context):
        processed.append(instance)
        if error is not None:
            raise error

    if not processed:
        log.warning("No validations were run")


def extract(context):
    """Convenience function for extraction"""
    processed = list()

    for instance, error in process('extractors', context):
        processed.append(instance)
        if error is not None:
            log.error(error)

    if not processed:
        log.warning("Nothing was extracted")


def conform(context):
    """Perform conform upon context `context`"""
    processed = list()

    for instance, error in process('conforms', context):
        processed.append(instance)
        if error is not None:
            log.error(error)

    if not processed:
        log.warning("Nothing was conformed")


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

    if not context:
        return log.info("No instances found.")

    validate(context)

    log.info("All instances valid")
