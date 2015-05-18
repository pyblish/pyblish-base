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
import time
import logging
import warnings
import traceback

# Local library
import pyblish.api

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
            auto_repair=False,
            include_optional=True,
            instances=None,
            logging_level=logging.INFO,
            **kwargs):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during selection.

    Arguments:
        context (pyblish.api.Context): Optional Context.
            Defaults to creating a new context each time.
        auto_repair (bool): Whether or not to attempt to automatically
            repair instances which fail validation.
        include_optional (bool): Should validation include plug-ins
            which has been defined as optional?
        logging_level (logging level): Optional level with which
            to log messages. Default is logging.INFO.

    Usage:
        >> publish()
        >> publish(context=Context())

    """

    assert context is None or isinstance(context, pyblish.api.Context)

    # Hidden argument
    _orders = kwargs.pop("orders", None) or (0, 1, 2, 3)
    assert not kwargs  # There are no more arguments

    errors = dict()
    context = context or pyblish.api.Context()
    for plugin in plugins or pyblish.api.discover():
        for instance, error in process(plugin, context):
            if error is not None:
                errors[error] = instance

        if errors and plugin.order >= 2:
            # Before proceeding with extraction, ensure
            # that there are no failed validators.
            log.warning("")  # newline
            log.warning("There were errors:")
            for error, instance in errors.iteritems():
                item = instance or "Context"
                log.warning("    %s: %s" % (item, error))

            break

    if not len(context):
        log.warning("No instances were found")

    return context


def process(plugin, context, instances=None):
    """Primary event loop

    Arguments:
        plugin (Plugin): Plug-in to process
        context (Context): Context to process
        instances (list, optional): Names of instances to process,
            names not in list will not be processed.

    .. note:: If an instance contains the data "publish" and that data is
        `False` the instance will not be processed.

    Injected data during processing:
    - `__is_processed__`: Whether or not the instance was processed
    - `__processed_by__`: Plugins which processed the given instance

    Returns:
        :meth:`process` returns a generator with (instance, error), with
            error defaulted to `None`. Each error is injected with a
            stack-trace of what went wrong, accessible via error.traceback.

    Yields:
        Tuple (Instance, Exception)

    """

    print "Args: %s, %s, %s" % (plugin, context, instances)

    try:
        plugin().process_context(context)

    except Exception as err:
        try:
            _, _, exc_tb = sys.exc_info()
            err.traceback = traceback.extract_tb(
                exc_tb)[-1]
        except:
            pass

        yield None, err

    finally:
        compatible_instances = pyblish.api.instances_by_plugin(
            instances=context, plugin=plugin)

        if compatible_instances:
            for instance in compatible_instances:
                # Limit instances to those specified in `instances`
                if instances is not None and \
                        instance.name not in instances:
                    plugin.log.debug("Skipping %s, "
                                     "not included in "
                                     "exclusive list (%s)" % (instance,
                                                              instances))
                    continue

                if instance.has_data("publish"):
                    if instance.data("publish", default=True) is False:
                        plugin.log.debug("Skipping %s, "
                                         "publish-flag was false" % instance)
                        continue

                elif not pyblish.config["publish_by_default"]:
                    plugin.log.debug("Skipping %s, "
                                     "no publish-flag was "
                                     "set, and publishing "
                                     "by default is False" % instance)
                    continue

                plugin.log.info("Processing instance: \"%s\"" % instance)

                # Inject data
                processed_by = instance.data("__processed_by__") or list()
                processed_by.append(plugin)
                instance.set_data("__processed_by__", processed_by)
                instance.set_data("__is_processed__", True)

                try:
                    plugin().process_instance(instance)
                    err = None

                except Exception as err:
                    try:
                        _, _, exc_tb = sys.exc_info()
                        err.traceback = traceback.extract_tb(
                            exc_tb)[-1]
                    except:
                        pass

                finally:
                    yield instance, err


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
    return _convenience("selectors", *args, **kwargs)


def validate(*args, **kwargs):
    """Convenience function for validation"""
    return _convenience("selectors", *args, **kwargs)


def extract(*args, **kwargs):
    """Convenience function for extraction"""
    return _convenience("extractors", *args, **kwargs)


def conform(*args, **kwargs):
    """Convenience function for conform"""
    return _convenience("conformers", *args, **kwargs)


def _convenience(type, *args, **kwargs):
    plugins = pyblish.api.discover(type=type)
    args = list(args)
    if len(args) > 1:
        args[1] = plugins
    else:
        kwargs["plugins"] = plugins
    return publish(*args, **kwargs)


def _format_paths(paths):
    """Return paths at one new each"""
    message = ""
    for path in paths:
        message += "{0}- {1}\n".format(TAB, path)
    return message[:-1]  # Discard last newline


def _format_plugins(plugins):
    message = ""
    for plugin in sorted(plugins, key=lambda p: p.__name__):
        line = "{tab}- {plug}".format(
            tab=TAB, plug=plugin.__name__)

        if hasattr(plugin, "families"):
            line = line.ljust(50) + " "
            for family in plugin.families:
                line += "%s, " % family
            line = line[:-2]

        line += "\n"

        message += line

    return message[:-1]


# For backwards compatibility
def publish_all(*args, **kwargs):
    warnings.warn("pyblish.util.publish_all has been deprecated; use publish()")
    return publish(*args, **kwargs)


def validate_all(*args, **kwargs):
    warnings.warn("pyblish.util.validate_all has been deprecated; use validate()")
    return validate(*args, **kwargs)

