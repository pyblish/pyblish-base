"""Convenience functions for general publishing"""

from __future__ import absolute_import

# Standard library
import logging
import warnings

# Local library
from . import api, logic, plugin, lib

log = logging.getLogger("pyblish.util")

__all__ = [
    "publish",
    "collect",
    "validate",
    "extract",
    "integrate",

    # Iterator counterparts
    "publish_iter",
    "collect_iter",
    "validate_iter",
    "extract_iter",
    "integrate_iter",
]


def publish(context=None, plugins=None, targets=None):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during collection.

    Arguments:
        context (Context, optional): Context, defaults to
            creating a new context
        plugins (list, optional): Plug-ins to include,
            defaults to results of discover()
        targets (list, optional): Targets to include for publish session.

    Returns:
        Context: The context processed by the plugins.

    Usage:
        >> context = plugin.Context()
        >> publish(context)     # Pass..
        >> context = publish()  # ..or receive a new

    """

    context = context if context is not None else api.Context()

    for _ in publish_iter(context, plugins, targets):
        pass

    return context


def publish_iter(context=None, plugins=None, targets=None):
    """Publish iterator

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during collection.

    Arguments:
        context (Context, optional): Context, defaults to
            creating a new context
        plugins (list, optional): Plug-ins to include,
            defaults to results of discover()
        targets (list, optional): Targets to include for publish session.

    Yields:
        tuple of dict and Context: A tuple is returned with a dictionary and
            the Context object. The dictionary contains all the result
            information of a plugin process, and the Context is the Context
            after the plugin has been processed.

    Usage:
        >> context = plugin.Context()
        >> for result in util.publish_iter(context):
               print result
        >> for result in util.publish_iter():
               print result

    """
    for result in _convenience_iter(context, plugins, targets):
        yield result

    api.emit("published", context=context)


def _convenience_iter(context=None, plugins=None, targets=None, order=None):
    # Must check against None, as objects be emptys
    context = api.Context() if context is None else context
    plugins = api.discover() if plugins is None else plugins

    if order is not None:
        plugins = list(
            Plugin for Plugin in plugins
            if lib.inrange(Plugin.order, order)
        )

    # Do not consider inactive plug-ins
    plugins = list(p for p in plugins if p.active)
    collectors = list(p for p in plugins if lib.inrange(
        number=p.order,
        base=api.CollectorOrder)
    )

    # Compute an approximation of all future tasks
    # NOTE: It's an approximation, because tasks are
    # dynamically determined at run-time by contents of
    # the context and families of contained instances;
    # each of which may differ between task.
    task_count = len(list(logic.Iterator(plugins, context, targets=targets)))

    # First pass, collection
    tasks_processed_count = 1
    for Plugin, instance in logic.Iterator(collectors,
                                           context,
                                           targets=targets):
        result = plugin.process(Plugin, context, instance)

        # Inject additional member for results here.
        result["progress"] = float(tasks_processed_count) / task_count

        tasks_processed_count += 1
        yield result

    # Exclude collectors from further processing
    plugins = list(p for p in plugins if p not in collectors)

    # Exclude plug-ins that do not have at
    # least one compatible instance.
    for Plugin in list(plugins):
        if Plugin.__instanceEnabled__:
            if not logic.instances_by_plugin(context, Plugin):
                plugins.remove(Plugin)

    # Mutable state, used in Iterator
    state = {
        "nextOrder": None,
        "ordersWithError": set()
    }

    # Second pass, the remainder
    for Plugin, instance in logic.Iterator(plugins,
                                           context,
                                           state,
                                           targets=targets):
        try:
            result = plugin.process(Plugin, context, instance)
            result["progress"] = (
                float(tasks_processed_count) / task_count
            )

            tasks_processed_count += 1
        except StopIteration:  # End of items
            raise

        except Exception:  # This is unexpected, most likely a bug
            log.error("An expected exception occurred.\n")
            raise

        else:
            # Make note of the order at which the
            # potential error error occured.
            if result["error"]:
                state["ordersWithError"].add(Plugin.order)

        if isinstance(result, Exception):
            log.error("An unexpected error happened: %s" % result)
            break

        error = result["error"]
        if error is not None:
            print(error)

        yield result


def collect(context=None, plugins=None, targets=None):
    """Convenience function for collection-only

     _________    . . . . .  .   . . . . . .   . . . . . . .
    |         |   .          .   .         .   .           .
    | Collect |-->. Validate .-->. Extract .-->. Integrate .
    |_________|   . . . . .  .   . . . . . .   . . . . . . .

    """

    context = context if context is not None else api.Context()
    for result in collect_iter(context, plugins, targets):
        pass

    return context


def validate(context=None, plugins=None, targets=None):
    """Convenience function for validation-only

    . . . . . .    __________    . . . . . .   . . . . . . .
    .         .   |          |   .         .   .           .
    . Collect .-->| Validate |-->. Extract .-->. Integrate .
    . . . . . .   |__________|   . . . . . .   . . . . . . .

    """

    context = context if context is not None else api.Context()
    for result in validate_iter(context, plugins, targets):
        pass

    return context


def extract(context=None, plugins=None, targets=None):
    """Convenience function for extraction-only

    . . . . . .   . . . . .  .    _________    . . . . . . .
    .         .   .          .   |         |   .           .
    . Collect .-->. Validate .-->| Extract |-->. Integrate .
    . . . . . .   . . . . .  .   |_________|   . . . . . . .

    """

    context = context if context is not None else api.Context()
    for result in extract_iter(context, plugins, targets):
        pass

    return context


def integrate(context=None, plugins=None, targets=None):
    """Convenience function for integration-only

    . . . . . .   . . . . .  .   . . . . . .    ___________
    .         .   .          .   .         .   |           |
    . Collect .-->. Validate .-->. Extract .-->| Integrate |
    . . . . . .   . . . . .  .   . . . . . .   |___________|

    """

    context = context if context is not None else api.Context()
    for result in integrate_iter(context, plugins, targets):
        pass

    return context


def collect_iter(context=None, plugins=None, targets=None):
    for result in _convenience_iter(context, plugins, targets,
                                    order=api.CollectorOrder):
        yield result

    api.emit("collected", context=context)


def validate_iter(context=None, plugins=None, targets=None):
    for result in _convenience_iter(context, plugins, targets,
                                    order=api.ValidatorOrder):
        yield result

    api.emit("validated", context=context)


def extract_iter(context=None, plugins=None, targets=None):
    for result in _convenience_iter(context, plugins, targets,
                                    order=api.ExtractorOrder):
        yield result

    api.emit("extracted", context=context)


def integrate_iter(context=None, plugins=None, targets=None):
    for result in _convenience_iter(context, plugins, targets,
                                    order=api.IntegratorOrder):
        yield result

    api.emit("integrated", context=context)


def _convenience(context=None, plugins=None, targets=None, order=None):
    context = context if context is not None else api.Context()

    for result in _convenience_iter(context, plugins, targets, order):
        pass

    return context


# Backwards compatibility
select = collect
conform = integrate
run = publish  # Alias


def publish_all(context=None, plugins=None):
    warnings.warn("pyblish.util.publish_all has been "
                  "deprecated; use publish()")
    return publish(context, plugins)


def validate_all(context=None, plugins=None):
    warnings.warn("pyblish.util.validate_all has been "
                  "deprecated; use collect() followed by validate()")
    context = collect(context, plugins)
    return validate(context, plugins)
