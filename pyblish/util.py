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

    # Keep track of state, so we can cancel on failed validation
    state = {
        "nextOrder": None,
        "ordersWithError": set()
    }

    test = api.registered_test()

    # Second pass, the remainder
    for Plugin, instance in logic.Iterator(plugins, context):
        state["nextOrder"] = Plugin.order

        if test(**state):
            log.error("Stopped due to: %s" % test(**state))
            break

        try:
            result = plugin.process(Plugin, context, instance)

        except:
            # This exception is unexpected
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
    """Convenience function for collection

     _________    . . . . .  .   . . . . . .   . . . . . . .
    |         |   .          .   .         .   .           .
    | Collect |-->. Validate .-->. Extract .-->. Integrate .
    |_________|   . . . . .  .   . . . . . .   . . . . . . . 

    """

    context = _convenience(0.5, context, plugins)
    api.emit("collected", context=context)
    return context


def validate(context=None, plugins=None):
    """Convenience function for collection through validation

     _________     __________    . . . . . .   . . . . . . .
    |         |   |          |   .         .   .           .
    | Collect |-->| Validate |-->. Extract .-->. Integrate .
    |_________|   |__________|   . . . . . .   . . . . . . . 

    """

    context = _convenience(1.5, context, plugins)
    api.emit("validated", context=context)
    return context


def extract(context=None, plugins=None):
    """Convenience function for collection through extraction

     _________     __________     _________    . . . . . . .
    |         |   |          |   |         |   .           .
    | Collect |-->| Validate |-->| Extract |-->. Integrate .
    |_________|   |__________|   |_________|   . . . . . . . 

    """

    context = _convenience(2.5, context, plugins)
    api.emit("extracted", context=context)
    return context


def integrate(context=None, plugins=None):
    """Convenience function for collection through end

     _________     __________     _________     ___________ 
    |         |   |          |   |         |   |           |
    | Collect |-->| Validate |-->| Extract |-->| Integrate |
    |_________|   |__________|   |_________|   |___________| 

    """

    context = _convenience(float("inf"), context, plugins)
    api.emit("integrated", context=context)
    return context


def _convenience(order, context=None, plugins=None):
    plugins = list(
        p for p in (api.discover() if plugins is None else plugins)
        if p.order < order
    )

    return publish(context, plugins)


# Backwards compatibility
select = collect
conform = integrate
run = publish  # Alias


def publish_all(*args, **kwargs):
    warnings.warn("pyblish.util.publish_all has been "
                  "deprecated; use publish()")
    return publish(*args, **kwargs)


def validate_all(*args, **kwargs):
    warnings.warn("pyblish.util.validate_all has been "
                  "deprecated; use validate()")
    return validate(*args, **kwargs)
