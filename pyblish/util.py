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
import sys
import logging
import warnings
import datetime
import traceback

# Local library
import pyblish.api
import pyblish.logic

log = logging.getLogger("pyblish")


__all__ = ["select",
           "validate",
           "extract",
           "conform",
           "publish",
           "publish_all",
           "validate_all",
           "process"]


def publish(context=None,
            plugins=None,
            **kwargs):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during selection.

    Arguments:
        context (pyblish.api.Context): Optional Context,
            defaults to creating a new context
        plugins (list): (Optional) Plug-ins to include,
            defaults to discover()

    Usage:
        >> context = pyblish.api.Context()
        >> publish(context)  # Pass..
        >> context = publish()  # ..or receive a new

    """

    assert context is None or isinstance(context, pyblish.api.Context)

    # Must check against None, as the
    # Context may come in empty.
    if context is None:
        context = pyblish.api.Context()

    if plugins is None:
        plugins = pyblish.api.discover()

    for result in pyblish.logic.process(
            func=process,
            plugins=plugins,
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            log.error("Stopped due to: %s (%s)" % (result, result.vars))
            break

        if isinstance(result, Exception):
            log.critical("Got an exception: %s" % result)
            break

    return context


# Utilities
def time():
    return datetime.datetime.now().strftime(
            pyblish.api.config["date_format"])


def process(plugin, context, instance=None):
    """Determine whether the given plug-in to be dependency injected"""
    if (hasattr(plugin, "process_instance")
            or hasattr(plugin, "process_context")):
        return _process_legacy(plugin, context, instance)
    else:
        return _process(plugin, context, instance)


def _process(plugin, context, instance=None):
    """Process plug-in given an optional Context and Instance

    Context and Instance are injected prior to processing.

    Returns result.

    """

    import time

    if "results" not in context.data():
        context.set_data("results", list())

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "error": None,
        "records": list(),
        "duration": None
    }

    plugin = plugin()

    provider = pyblish.plugin.Provider()
    provider.inject("context", context)
    provider.inject("instance", instance)

    records = list()
    handler = MessageHandler(records)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    __start = time.time()

    try:
        provider.invoke(plugin.process)
        result["success"] = True
    except Exception as error:
        extract_traceback(error)
        result["error"] = error

    __end = time.time()

    for record in records:
        result["records"].append(record)

    # Restore balance to the world
    root_logger.removeHandler(handler)

    result["duration"] = (__end - __start) * 1000  # ms

    context.data("results").append(result)

    return result


def _process_legacy(plugin, context, instance=None):
    import time

    if "results" not in context.data():
        context.set_data("results", list())

    if not hasattr(plugin, "process_context"):
        plugin.process_context = lambda self, context: None

    if not hasattr(plugin, "process_instance"):
        plugin.process_instance = lambda self, instance: None

    result = {
        "success": False,
        "plugin": plugin,
        "instance": instance,
        "error": None,
        "records": list(),
        "duration": None
    }

    records = list()
    handler = MessageHandler(records)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    __start = time.time()

    try:
        plugin().process_context(context)
        result["success"] = True
    except Exception as exc:
        extract_traceback(exc)
        result["error"] = exc

    if instance is not None:
        try:
            plugin().process_instance(instance)
            result["success"] = True
        except Exception as exc:
            extract_traceback(exc)
            result["error"] = exc

    __end = time.time()

    for record in records:
        result["records"].append(record)

    # Restore balance to the world
    root_logger.removeHandler(handler)

    result["duration"] = (__end - __start) * 1000  # ms

    context.data("results").append(result)

    return result


def process_all(plugin, context):
    """Convenience method of the above :func:`process`

    Arguments:
        plugin (Plugin): Plug-in to process
        context (Context): Context to process

    Return:
        None

    """

    for instance, error in process(plugin, context):
        if error is not None:
            raise error


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
    plugins = [p for p in pyblish.api.discover()
               if p.order < order]

    args = list(args)
    if len(args) > 1:
        args[1] = plugins
    else:
        kwargs["plugins"] = plugins
    return publish(*args, **kwargs)


class MessageHandler(logging.Handler):
    def __init__(self, records, *args, **kwargs):
        # Not using super(), for compatibility with Python 2.6
        logging.Handler.__init__(self, *args, **kwargs)
        self.records = records

    def emit(self, record):
        self.records.append(record)


def extract_traceback(exception):
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)


# Backwards compatibility
def publish_all(*args, **kwargs):
    warnings.warn("pyblish.util.publish_all has been "
                  "deprecated; use publish()")
    return publish(*args, **kwargs)


def validate_all(*args, **kwargs):
    warnings.warn("pyblish.util.validate_all has been "
                  "deprecated; use validate()")
    return validate(*args, **kwargs)
