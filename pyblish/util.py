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

    try:
        for result in pyblish.logic.process(
                plugins=plugins,
                process=process,
                context=context):
            pass
    except pyblish.logic.TestFailed:
        pass

    return context


# Utilities
def time():
    return datetime.datetime.now().strftime(
            pyblish.api.config["date_format"])


# def test(**vars):
#     """Evaluate whether or not to continue processing"""
#     if vars["order"] >= 2:  # If validation is done
#         for order in vars["errorOrders"]:
#             if order < 2:  # Were there any error before validation?
#                 return False
#     return True


# def coprocess(plugins, process, context):
#     """Co-routine

#     Takes callables and data as input, and performs
#     logical operations on them

#     """

#     def gen(plugin, context):
#         """Generate pair of context/instance"""
#         instances = pyblish.api.instances_by_plugin(context, plugin)
#         if len(instances) > 0:
#             for instance in instances:
#                 yield context, instance
#         else:
#             yield context, None

#     vars = {
#         "order": None,
#         "errorOrders": list()
#     }

#     results = list()

#     for plugin in plugins:
#         vars["order"] = plugin.order

#         if test(**vars):
#             for context, instance in gen(plugin, context):
#                 result = process(plugin, context, instance)
#                 if result["error"]:
#                     vars["errorOrders"].append(plugin.order)

#                 results.append(result)
#                 yield result

#         else:
#             # Before proceeding with extraction, ensure
#             # that there are no failed validators.
#             log.warning("")  # newline
#             log.warning("There were errors:")
#             for result in results:
#                 item = result["instance"] or "Context"
#                 log.warning("%s: %s" % (item, result["error"]))

#             break


def process(plugin, context, instance=None):
    """Determine whether the given plug-in to be dependency injected"""
    if (hasattr(plugin, "process_instance")
            or hasattr(plugin, "process_context")):
        return _process_legacy(plugin, context, instance)
    else:
        return _process(plugin, context, instance)


def _process(plugin, context, instance=None):
    """A single process

    Context is always present, an instance is optional.
    Whether an instance is used depends on:

    1. Whether one exists
    2. Whether it is asked for

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

    provider = pyblish.plugin.Provider()
    provider.inject("context", context)
    provider.inject("instance", instance)

    plugin = plugin()  # Initialise

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

    result["duration"] = (__end - __start) * 1000  # ms

    context.data("results").append(result)

    return result


# def process(plugin, context, instances=None):
#     """Determine whether the given plug-in to be dependency injected"""
#     if (hasattr(plugin, "process_instance")
#             or hasattr(plugin, "process_context")):
#         return _process_legacy(plugin, context, instances)
#     else:
#         return _process(plugin, context, instances)


# def _process_legacy(plugin, context, instances=None):
#     """Primary event loop

#     Arguments:
#         plugin (Plugin): Plug-in to process
#         context (Context): Context to process
#         instances (list, optional): Names of instances to process,
#             names not in list will not be processed.

#     .. note:: If an instance contains the data "publish" and that data is
#         `False` the instance will not be processed.

#     Injected data during processing:
#     - `__is_processed__`: Whether or not the instance was processed
#     - `__processed_by__`: Plugins which processed the given instance

#     Returns:
#         :meth:`process` returns a generator with (instance, error), with
#             error defaulted to `None`. Each error is injected with a
#             stack-trace of what went wrong, accessible via error.traceback.

#     Yields:
#         Tuple (Instance, Exception)

#     """

#     # Patch up now-missing processing functions
#     if not hasattr(plugin, "process_context"):
#         plugin.process_context = lambda self, context: None

#     if not hasattr(plugin, "process_instance"):
#         plugin.process_instance = lambda self, instance: None

#     try:
#         plugin().process_context(context)

#     except Exception as err:
#         try:
#             _, _, exc_tb = sys.exc_info()
#             err.traceback = traceback.extract_tb(
#                 exc_tb)[-1]
#         except:
#             pass

#         yield None, err

#     finally:
#         for instance in pyblish.api.instances_by_plugin(
#                 context, plugin):

#             # Limit instances to those specified in `instances`
#             if instances is not None and \
#                     instance.name not in instances:
#                 plugin.log.debug("Skipping %s, "
#                                  "not included in "
#                                  "exclusive list (%s)" % (instance,
#                                                           instances))
#                 continue

#             if instance.has_data("publish"):
#                 if instance.data("publish", default=True) is False:
#                     plugin.log.debug("Skipping %s, "
#                                      "publish-flag was false" % instance)
#                     continue

#             elif not pyblish.api.config["publish_by_default"]:
#                 plugin.log.debug("Skipping %s, "
#                                  "no publish-flag was "
#                                  "set, and publishing "
#                                  "by default is False" % instance)
#                 continue

#             plugin.log.info("Processing instance: \"%s\"" % instance)

#             # Inject data
#             processed_by = instance.data("__processed_by__") or list()
#             processed_by.append(plugin)
#             instance.set_data("__processed_by__", processed_by)
#             instance.set_data("__is_processed__", True)

#             try:
#                 plugin().process_instance(instance)
#                 err = None

#             except Exception as err:
#                 try:
#                     _, _, exc_tb = sys.exc_info()
#                     err.traceback = traceback.extract_tb(
#                         exc_tb)[-1]
#                 except:
#                     pass

#             finally:
#                 yield instance, err


# def _process(plugin, context, instances=None):
#     """Dependency Injection event loop

#     Plug-ins are initialised once and only once, whereas
#     it's call to :meth:`Plugin.process` is called once per
#     available instance.

#     """

#     def gen(plugin, context):
#         """Generate pair of context/instance"""
#         instances = pyblish.api.instances_by_plugin(context, plugin)
#         if instances:
#             for instance in instances:
#                 yield context, instance
#         else:
#             yield context, None

#     provider = pyblish.plugin.Provider()
#     provider.inject("context", context)

#     plugin = plugin()  # Initialise

#     for context, instance in gen(plugin, context):
#         provider.inject("instance", instance)

#         plugin.log.info("%s processing: %s" % (
#             plugin, provider.args(plugin.process)))

#         if instance is not None:
#             processed_by = instance.data("__processed_by__") or list()
#             processed_by.append(plugin)
#             instance.set_data("__processed_by__", processed_by)
#             instance.set_data("__is_processed__", True)

#         try:
#             provider.invoke(plugin.process)
#             err = None
#         except Exception as err:
#             _, _, exc_tb = sys.exc_info()
#             err.traceback = traceback.extract_tb(exc_tb)[-1]

#         yield instance, err


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
    return _convenience(
        ["selectors"],
        *args, **kwargs)


def validate(*args, **kwargs):
    """Convenience function for validation"""
    return _convenience(
        ["selectors",
         "validators"],
        *args, **kwargs)


def extract(*args, **kwargs):
    """Convenience function for extraction"""
    return _convenience(
        ["selectors",
         "validators",
         "extractors"],
        *args, **kwargs)


def conform(*args, **kwargs):
    """Convenience function for conform"""
    return _convenience(
        ["selectors",
         "validators",
         "extractors",
         "conformers"],
        *args, **kwargs)


def _convenience(types, *args, **kwargs):
    plugins = list()
    for type in types:
        plugins.extend(pyblish.api.discover(type=type))
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
