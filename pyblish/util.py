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

log = logging.getLogger()

# TAB = "    "
# LOG_TEMPATE = "    %(levelname)-8s %(message)s"
# SCREEN_WIDTH = 80

# Messages
# NO_INSTANCES_ERROR = "Cancelled due to not finding any instances"
# SELECTION_ERROR = "Selection failed"
# VALIDATION_ERROR = "Validation failed"

# Templates
# AUTO_REPAIR = "There were errors, attempting to auto-repair.."
# COMMITTED_TEMPLATE = "{tab}Committed to: {dir}"
# CONFORMED_TEMPLATE = "{tab}Conformed to: {dir}"
# FAILED_VALIDATION_TEMPLATE = "{tab}- \"{instance}\": {exception} ({plugin})"
# SUCCESS_TEMPLATE = "Processed {num} instance{s} {status} in {seconds}s"
# TRACEBACK_TEMPLATE = "(Line {line} in \"{file}\" @ \"{func}\")"
# ERROR_TEMPLATE = "{tab}{instance}: {error} {traceback}"
# VALIDATIONS_FAILED_TEMPLATE = """
# These validations failed:
# {failures}"""

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
            log.warning()  # newline
            log.warning("There were errors:")
            for error, instance in errors.iteritems():
                item = instance or "Context"
                log.warning("    %s: %s" % (item, error))

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


# class Publish(object):
#     """Publishing operator

#     Arguments:
#         context (pyblish.api.Context): Optional Context.
#             Defaults to creating a new context each time.
#         auto_repair (bool): Whether or not to attempt to automatically
#             repair instances which fail validation.
#         include_optional (bool): Should validation include plug-ins
#             which has been defined as optional?
#         logging_level (logging level): Optional level with which
#             to log messages. Default is logging.INFO.

#     """

#     log = logging.getLogger()

#     @property
#     def duration(self):
#         return "%.2f" % (self._time["end"] - self._time["start"])

#     def __init__(self,
#                  context=None,
#                  auto_repair=False,
#                  include_optional=True,
#                  instances=None,
#                  logging_level=logging.INFO):

#         if context is None:
#             context = pyblish.api.Context()

#         self.context = context
#         self.orders = (0, 1, 2, 3)
#         self.repair = auto_repair
#         self.optional = include_optional
#         self.logging_level = logging_level
#         self.instances = None

#         self._plugins = pyblish.plugin.discover()
#         self._conf = pyblish.api.config
#         self._time = {"start": None, "end": None}
#         self._errors = list()

#     def process(self):
#         """Process all instances within the given context"""
#         self._time["start"] = time.time()
#         self._log_intro()

#         log_summary = False

#         # Initialise pretty-printing for plug-ins
#         self._init_log()

#         try:
#             for order in self.orders:
#                 self.process_order(order)

#         except pyblish.api.NoInstancesError as exc:
#             self.log.warning(NO_INSTANCES_ERROR)

#         except pyblish.api.SelectionError:
#             self.log.error(SELECTION_ERROR)

#         except pyblish.api.ValidationError as exc:
#             self.log.error(VALIDATION_ERROR)

#             failures = list()
#             for error in exc.errors:
#                 failures.append(FAILED_VALIDATION_TEMPLATE.format(
#                     instance=error.instance,
#                     tab=TAB,
#                     exception=error,
#                     plugin=error.plugin.__name__))
#             print VALIDATIONS_FAILED_TEMPLATE.format(
#                 failures="\n".join(failures))

#         except Exception as exc:
#             self.log.error("Unhandled exception: %s" % exc)

#         else:
#             log_summary = True

#         # Clear context
#         self._time["end"] = time.time()

#         print  # newline
#         print "-" * 80

#         self._log_time()

#         if log_summary:
#             self._log_summary()

#         self._reset_log()
#         self._log_success()

#     def process_order(self, order):
#         """Process context using plug-ins with the specified `order`

#         Arguments:
#             order (int): Order of plug-ins with which to process context.

#         Raises:
#             pyblish.api.SelectionError: When selection fails
#             pyblish.api.ValidationError: When validation fails

#         """

#         if order != 0 and not self.context:
#             # If there aren't any instances after selection,
#             # there is no point in going on.
#             raise pyblish.api.NoInstancesError

#         order_errors = list()
#         for plugin in self._plugins:

#             if plugin.order != order:
#                 continue

#             plugin_errors = self.process_plugin(plugin)
#             order_errors.extend(plugin_errors)

#             if not plugin_errors:
#                 continue

#             # Before proceeding with extraction, ensure
#             # that there are no failed validators.
#             self.log.warning("There were errors:")
#             for error in plugin_errors:
#                 self._log_error(error.instance, error)

#         if not order_errors:
#             return

#         # If the error occurred during selection or validation,
#         # we don't want to continue.
#         if order == 0:
#             raise pyblish.api.SelectionError

#         if order == 1:
#             exception = pyblish.api.ValidationError
#             exception.errors = order_errors
#             raise exception

#     def process_plugin(self, plugin):
#         """Process context using a single plugin

#         Arguments:
#             plugin (Plugin): Plug-in used to process context

#         Returns:
#             List of errors occurred for `plugin`

#         """

#         errors = list()

#         # Do not include optional plug-ins
#         if plugin.optional and self.optional is False:
#             self._log_plugin(plugin, suffix="(optional and skipped)")
#             return errors

#         self._log_plugin(plugin)

#         for instance, error in process(plugin, self.context):
#             if instance is None and error is None:
#                 self.log.debug("Skipped, no compatible instances.")
#                 continue

#             if error is None:
#                 continue

#             repaired = False
#             if plugin.order == 1 and self.repair:
#                 repaired = self._repair(plugin, instance)

#             if not repaired:
#                 errors.append(error)

#                 # Inject data for logging
#                 error.instance = instance
#                 error.plugin = plugin

#                 # Store global reference for self._report()
#                 self._errors.append(error)

#         return errors

#     def _repair(self, plugin, instance):
#         if hasattr(plugin, "repair_instance"):
#             self.log.warning(AUTO_REPAIR)
#             try:
#                 plugin().repair_instance(instance)

#             except Exception as err:
#                 self.log.warning("Could not auto-repair..")
#                 self._log_error(instance, err)

#             else:
#                 self.log.info("Auto-repair successful")
#                 return True

#         return False

#     def _init_log(self):
#         self.log._handlers = list(self.log.handlers)
#         self.log.handlers[:] = []

#         formatter = logging.Formatter(LOG_TEMPATE)

#         stream_handler = logging.StreamHandler()
#         stream_handler.setFormatter(formatter)
#         self.log.addHandler(stream_handler)

#         self.log.setLevel(self.logging_level)

#     def _reset_log(self):
#         self.log.handlers[:] = self.log._handlers
#         self.log.setLevel(logging.INFO)

#     def _log_plugin(self, plugin, suffix=""):
#         if hasattr(plugin, "name"):
#             name = "%s (%s) %s" % (plugin.__name__, plugin.name, suffix)
#         else:
#             name = plugin.__name__

#         print "{plugin}...".format(
#             tab=TAB,
#             plugin=name)

#     def _log_intro(self):
#         """Provide a preface to what is about to happen

#         Including:
#             - Pyblish version
#             - User configuration
#             - Available paths
#             - Available plug-ins

#         """

#         intro = """
# {line}
# pyblish version {version}
# {line}

# Available plugin paths:
# {paths}

# Available plugins:
# {plugins}
# """

#         message = intro.format(
#             line="-" * SCREEN_WIDTH,
#             version=pyblish.__version__,
#             paths=_format_paths(pyblish.api.plugin_paths()),
#             plugins=_format_plugins(self._plugins))

#         message += "\n{line}\nProcessing\n".format(line="-" * 80)
#         print message

#     def _log_error(self, instance, error):
#         """Format outputted error message

#         Including:
#             - Instance involved in error
#             - File name in which the error occurred
#             - Function/method of error
#             - Line number of error

#         Arguments:
#             instance (pyblish.api.Instance): Instance involved in error
#             error (Exception): Error to format

#         Returns:
#             Error as pretty-formatted string

#         """

#         traceback = getattr(error, "traceback", None)

#         if traceback:
#             fname, line_number, func, exc = traceback
#             traceback = (TRACEBACK_TEMPLATE.format(line=line_number,
#                                                    file=fname,
#                                                    func=func))

#         self.log.error(ERROR_TEMPLATE.format(
#             tab=TAB,
#             instance=instance,
#             error=error,
#             traceback=traceback if traceback else ""))

#     def _log_time(self):
#         """Return time-taken message"""
#         message = 'Time taken: %s' % self.duration
#         print message.rjust(SCREEN_WIDTH)

#     def _log_success(self):
#         """Log a success message"""
#         processed_instances = list()

#         for instance in self.context:
#             if not instance.data('__is_processed__'):
#                 continue
#             processed_instances.append(instance)

#         if self.context and not processed_instances:
#             self.log.warning("Instances were found, but none were processed")
#             return

#         if not self.context:
#             self.log.warning("No instances were found")
#             return

#         status = "successfully without errors"
#         if self._errors:
#             status = "with errors"

#         num_processed_instances = len(processed_instances)
#         (self.log.warning if self._errors else self.log.info)(
#             SUCCESS_TEMPLATE.format(
#                 num=num_processed_instances,
#                 s="s" if num_processed_instances > 1 else "",
#                 status=status,
#                 seconds=self.duration))

#     def _log_summary(self):
#         """Layout summary for `context`"""
#         message = "Summary:\n"

#         for instance in self.context:
#             is_processed = instance.data("__is_processed__")
#             processed_by = instance.data("__processed_by__")
#             commit_dir = instance.data("commit_dir")
#             conform_dir = instance.data("conform_dir")

#             _message = "{tab}- \"{inst}\" ".format(
#                 tab=TAB,
#                 inst=instance)

#             _message += "processed by:"

#             if is_processed:
#                 for _plugin in processed_by or list():
#                     _message += " \"%s\"," % _plugin.__name__
#                 _message = _message[:-1]

#             else:
#                 _message += " None"

#             message += _message + "\n"

#             if commit_dir:
#                 message += COMMITTED_TEMPLATE.format(
#                     tab=TAB*2, dir=commit_dir) + "\n"

#             if conform_dir:
#                 message += CONFORMED_TEMPLATE.format(
#                     tab=TAB*2, dir=conform_dir) + "\n"

#         print  # newline
#         print message

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

