"""Conveinence function for Pyblish

Attributes:
    TAB: Number of spaces for a tab
    LOG_TEMPATE: Template used for logging coming from
        plug-ins
    SCREEN_WIDTH: Default width at which logging and printing
        will (attempt to) restrain to.
    logging_handlers: Record of handlers at the start of
        importing this module. This module will modify the
        currently handlers and restore then once finished.
    log: Current logger
    intro_message: Message printed upon initiating a publish.

"""

from __future__ import absolute_import

# Standard library
import logging
import warnings

# Local library
import pyblish
import pyblish.lib
import pyblish.logic
import pyblish.plugin

log = logging.getLogger("pyblish")


def publish(context=None, plugins=None, **kwargs):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during selection.

    Arguments:
        context (pyblish.plugin.Context): Optional Context,
            defaults to creating a new context
        plugins (list): (Optional) Plug-ins to include,
            defaults to discover()

    Usage:
        >> context = pyblish.plugin.Context()
        >> publish(context)  # Pass..
        >> context = publish()  # ..or receive a new

    """

    assert context is None or isinstance(context, pyblish.plugin.Context)

    # Must check against None, as the
    # Context may come in empty.
    if context is None:
        context = pyblish.plugin.Context()

    if plugins is None:
        plugins = pyblish.plugin.discover()

    for result in pyblish.logic.process(
            func=pyblish.plugin.process,
            plugins=plugins,
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            log.error("Stopped due to: %s (%s)" % (result, result.vars))
            break

    return context


def select(*args, **kwargs):
    """Convenience function for selection"""
    return _convenience(1, *args, **kwargs)


def validate(*args, **kwargs):
    """Convenience function for validation"""
    return _convenience(2, *args, **kwargs)


def extract(*args, **kwargs):
    """Convenience function for extraction"""
    return _convenience(3, *args, **kwargs)


def conform(*args, **kwargs):
    """Convenience function for conform"""
    return _convenience(4, *args, **kwargs)


def _convenience(order, *args, **kwargs):
    plugins = [p for p in pyblish.plugin.discover()
               if p.order < order]

    args = list(args)
    if len(args) > 1:
        args[1] = plugins
    else:
        kwargs["plugins"] = plugins
    return publish(*args, **kwargs)


# Backwards compatibility
def publish_all(*args, **kwargs):
    warnings.warn("pyblish.util.publish_all has been "
                  "deprecated; use publish()")
    return publish(*args, **kwargs)


def validate_all(*args, **kwargs):
    warnings.warn("pyblish.util.validate_all has been "
                  "deprecated; use validate()")
    return validate(*args, **kwargs)
