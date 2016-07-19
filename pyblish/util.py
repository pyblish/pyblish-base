"""Conveinence functions for general publishing"""

from __future__ import absolute_import

# Standard library
import logging
import warnings

# Local library
from . import api, logic, plugin, lib

log = logging.getLogger("pyblish.util")


def publish(context=None, plugins=None):
    """Publish everything

    This function will process all available plugins of the
    currently running host, publishing anything picked up
    during collection.

    Arguments:
        context (Context, optional): Context, defaults to
            creating a new context
        plugins (list, optional): Plug-ins to include,
            defaults to results of discover()

    Usage:
        >> context = plugin.Context()
        >> publish(context)     # Pass..
        >> context = publish()  # ..or receive a new

    """

    # Must check against None, as objects be emptys
    context = api.Context() if context is None else context
    plugins = api.discover() if plugins is None else plugins

    # Do not consider inactive plug-ins
    plugins = list(p for p in plugins if p.active)
    collectors = list(p for p in plugins if lib.inrange(
        number=p.order,
        base=api.CollectorOrder)
    )

    # First pass, collection
    for Plugin, instance in logic.Iterator(collectors, context):
        plugin.process(Plugin, context, instance)

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
    for Plugin, instance in logic.Iterator(plugins, context, state):
        try:
            result = plugin.process(Plugin, context, instance)

        except StopIteration:  # End of items
            raise

        except:  # This is unexpected, most likely a bug
            log.error("An exception occurred.\n")
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

    api.emit("published", context=context)

    return context


def collect(context=None, plugins=None):
    """Convenience function for collection-only

     _________    . . . . .  .   . . . . . .   . . . . . . .
    |         |   .          .   .         .   .           .
    | Collect |-->. Validate .-->. Extract .-->. Integrate .
    |_________|   . . . . .  .   . . . . . .   . . . . . . .

    """

    context = _convenience(api.CollectorOrder, context, plugins)
    api.emit("collected", context=context)
    return context


def validate(context=None, plugins=None):
    """Convenience function for validation-only

    . . . . . .    __________    . . . . . .   . . . . . . .
    .         .   |          |   .         .   .           .
    . Collect .-->| Validate |-->. Extract .-->. Integrate .
    . . . . . .   |__________|   . . . . . .   . . . . . . .

    """

    context = _convenience(api.ValidatorOrder, context, plugins)
    api.emit("validated", context=context)
    return context


def extract(context=None, plugins=None):
    """Convenience function for extraction-only

    . . . . . .   . . . . .  .    _________    . . . . . . .
    .         .   .          .   |         |   .           .
    . Collect .-->. Validate .-->| Extract |-->. Integrate .
    . . . . . .   . . . . .  .   |_________|   . . . . . . .

    """

    context = _convenience(api.ExtractorOrder, context, plugins)
    api.emit("extracted", context=context)
    return context


def integrate(context=None, plugins=None):
    """Convenience function for integration-only

    . . . . . .   . . . . .  .   . . . . . .    ___________
    .         .   .          .   .         .   |           |
    . Collect .-->. Validate .-->. Extract .-->| Integrate |
    . . . . . .   . . . . .  .   . . . . . .   |___________|

    """

    context = _convenience(api.IntegratorOrder, context, plugins)
    api.emit("integrated", context=context)
    return context


def _convenience(order, context=None, plugins=None):
    plugins = list(
        p for p in (api.discover() if plugins is None else plugins)
        if lib.inrange(p.order, order)
    )

    return publish(context, plugins)


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
