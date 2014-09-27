"""Entry-point of Pyblish

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
import os
import time
import logging
import numbers

# Local library
import pyblish.api

TAB = "    "
LOG_TEMPATE = "{tab}%(levelname)-8s %(message)s".format(tab=TAB)
SCREEN_WIDTH = 80

logging_handlers = logging.getLogger().handlers[:]
log = logging.getLogger('pyblish.main')

intro_message = """
%s
pyblish version {version}
%s

User Configuration @ {user_path}

Available plugin paths:
{paths}

Available plugins:
{plugins}
""" % ("-" * SCREEN_WIDTH, "-" * SCREEN_WIDTH)

__all__ = ['select',
           'validate',
           'extract',
           'conform',
           'publish',
           'publish_all']


def _setup_log(root='', level=logging.WARNING):
    log = logging.getLogger(root)
    log.handlers[:] = []

    formatter = logging.Formatter(LOG_TEMPATE)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    log.setLevel(level)

    return log


def _reset_log():
    log = logging.getLogger()
    log.handlers[:] = logging_handlers[:]
    log.setLevel(logging.INFO)


def _format_time(start, finish):
    """Return right-aligned time-taken message"""
    message = 'Time taken: %.2fs' % (finish - start)
    return message.rjust(SCREEN_WIDTH)


def _format_paths(paths):
    """Return paths at one new each"""
    message = ''
    for path in paths:
        message += "{0}- {1}\n".format(TAB, path)
    return message[:-1]  # Discard last newline


def _format_plugins(plugins):
    message = ''
    for plugin in sorted(plugins, key=lambda p: p.__name__):
        line = "{tab}- {plug}".format(
            tab=TAB, plug=plugin.__name__)

        if hasattr(plugin, 'families'):
            line = line.ljust(50) + " "
            for family in plugin.families:
                line += "%s, " % family
            line = line[:-2]

        line += "\n"

        message += line

    return message[:-1]


def publish(context=None, types=None, delay=None, logging_level=logging.INFO):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during selection.

    Arguments:
        context (pyblish.api.Context): Optional Context.
            Defaults to creating a new context each time.
        types (list): Optional list of strings with names of types
            to perform. Default is to perform all types.
        delay (float): Add artificial delay to the processing
            of each plug-in. Used in debugging.
        logging_level (logging level): Optional level with which
            to log messages. Default is logging.INFO.

    Usage:
        >> publish()
        >> publish(context=Context())
        >> publish(types=('selectors', 'extractors'))
    """

    assert context is None or isinstance(context, pyblish.api.Context)
    assert types is None or isinstance(types, tuple)
    assert delay is None or isinstance(delay, numbers.Number)

    _start_time = time.time()  # Benchmark

    exception = None
    non_critical_errors = None

    if context is None:
        pyblish.api.Context.delete()
        context = pyblish.api.Context()

    try:
        _setup_log(level=logging_level)
        non_critical_errors = _publish(context,
                                       types=types,
                                       delay=delay)

    except pyblish.api.NoInstancesError as err:
        log.warning("Cancelled due to not finding any instances")
        exception = err

    except (pyblish.api.SelectionError, pyblish.api.ValidationError) as err:
        log.warning("Cancelled due to one or more errors")
        exception = err

    finally:
        pyblish.api.Context.delete()

        print  # newline
        print "-" * 80
        print _format_time(_start_time, time.time())
        print "Summary:"

        _reset_log()

        num_processed_instances = 0
        for instance in context:
            if instance.data('__is_processed__'):
                num_processed_instances += 1

                _message = "{tab}- \"{inst}\" processed by:".format(
                    tab=TAB,
                    inst=instance)

                for _plugin in instance.data('__processed_by__',
                                             default=list()):
                    _message += " \"%s\"," % _plugin.__name__
                print _message[:-1]

            commit_dir = instance.data('commit_dir')
            conform_dirs = instance.data('conform_dirs')

            if commit_dir:
                print "{tab}Committed to: {dir}".format(
                    tab=TAB*2, dir=commit_dir)

            if conform_dirs:
                print "{tab}Conformed to: {dir}".format(
                    tab=TAB*2, dir=", ".join(conform_dirs))

        print  # newline

        if exception:
            if isinstance(exception, pyblish.api.ValidationError):
                print "These validations failed:"
                for exception in exception.errors:
                    print "{tab}{err}".format(
                        tab=TAB, err=exception)
                print  # newline
                log.error("Validation failed")

            elif isinstance(exception, pyblish.api.SelectionError):
                log.error("Selection failed")

            elif isinstance(exception, pyblish.api.NoInstancesError):
                log.warning("No instances were found")

        else:
            if num_processed_instances:

                log_ = log.info
                status = "successfully without errors"
                if non_critical_errors:
                    log_ = log.warning
                    status = "with errors"

                duration = "%.3f" % (time.time() - _start_time)

                log_(
                    "Processed {num} instance{s} {status} "
                    "in {seconds}s".format(
                        num=num_processed_instances,
                        s="s" if num_processed_instances > 1 else "",
                        status=status,
                        seconds=duration))
            else:
                log.warning("Instances were found, but none were processed")

    return context


# Backwards compatibility
publish_all = publish


def _format_error(instance, error):
    """Format outputted error message

    Including:
        - Instance involved in error
        - File name in which the error occurred
        - Function/method of error
        - Line number of error

    Arguments:
        instance (pyblish.api.Instance): Instance involved in error
        error (Exception): Error to format

    Returns:
        Error as pretty-formatted string

    """

    traceback = getattr(error, 'traceback', None)

    if traceback:
        fname, line_number, func, exc = traceback
        traceback = ("(Line {line} in \"{file}\" "
                     "@ \"{func}\"".format(line=line_number,
                                           file=fname,
                                           func=func))

    return "{tab}{i}: {e} {tb}".format(
        tab=TAB,
        i=instance,
        e=error,
        tb=traceback if traceback else '')


def _publish(context, types, delay):
    """Implementation of publish()"""

    all_types = ('selectors',
                 'validators',
                 'extractors',
                 'conformers')

    if not types:
        types = all_types

    for typ in types:
        if not typ in all_types:
            log.error("Unrecognised type specified: %s" % typ)
            return

    plugin_paths = pyblish.api.plugin_paths()
    plugins = pyblish.api.discover(paths=plugin_paths)

    user_config_path = pyblish.api.config['USERCONFIGPATH']
    has_user_config = os.path.isfile(user_config_path)

    print (
        intro_message.format(
            version=pyblish.__version__,
            user_path=user_config_path if has_user_config else "None",
            paths=_format_paths(plugin_paths),
            plugins=_format_plugins(plugins)))

    print "{line}\nProcessing\n".format(line="-" * 80)

    # Errors that won't abort the publish
    non_critical_errors = False

    for typ in types:

        plugins = pyblish.api.discover(typ, paths=plugin_paths)

        if typ != 'selectors' and not context:
            # If selection is done, yet there are no instances,
            # it means nothing will be processed in subsequent steps.
            raise pyblish.api.NoInstancesError

        for plugin in plugins:
            print "{plugin}...".format(tab=TAB, plugin=plugin.__name__)

            errors = {}

            if delay:
                time.sleep(delay)

            for instance, error in plugin().process(context):
                if error is not None:
                    errors[error] = instance

            if errors:
                # Before proceeding with extraction, ensure
                # that there are no failed validators.
                log.warning("There were errors:")
                for error, instance in errors.iteritems():
                    error_message = _format_error(instance, error)
                    log.error(error_message)
                    non_critical_errors = True

                if typ not in ('extractors', 'conformers'):
                    # If the error occurred during selection
                    # or validation, we don't want to continue.
                    if typ == 'selectors':
                        err = pyblish.api.SelectionError
                    else:
                        err = pyblish.api.ValidationError

                    err.errors = errors
                    raise err  # Handled in publish()

    return non_critical_errors


def validate_all(*args, **kwargs):
    if not 'types' in kwargs:
        kwargs['types'] = ('selectors', 'validators',)

    publish(*args, **kwargs)


def select(*args, **kwargs):
    """Convenience function for selection"""
    if not 'types' in kwargs:
        kwargs['types'] = ('selectors',)

    publish(*args, **kwargs)


def validate(*args, **kwargs):
    """Convenience function for validation"""
    if not 'types' in kwargs:
        kwargs['types'] = ('validators',)

    publish(*args, **kwargs)


def extract(*args, **kwargs):
    """Convenience function for extraction"""
    if not 'types' in kwargs:
        kwargs['types'] = ('extractors',)

    publish(*args, **kwargs)


def conform(*args, **kwargs):
    """Convenience function for conform"""
    if not 'types' in kwargs:
        kwargs['types'] = ('conformers',)

    publish(*args, **kwargs)
