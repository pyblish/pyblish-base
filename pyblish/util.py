"""Conveinence functions for general publishing"""

from __future__ import absolute_import

# Standard library
import logging
import warnings

# Local library
from . import api, logic, plugin, lib

log = logging.getLogger("pyblish.util")


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

    # Need to generate a Context object if None is passed. This is because,
    # if None is passed the publish iterator won't process the context and not
    # return anything.
    context = api.Context() if context is None else context

    # Since the Context object is a singleton, we can just run though the
    # publish iterator without assigning any variables.
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
        >> for result, context in util.publish_iter(context):
               print result
               print context
        >> for result, context in util.publish_iter():
               print result
               print context

    """

    percentage = 0.0

    # Include "default" target when no targets are requested.
    if targets is None:
        targets = ["default"]

    # Must check against None, as objects be emptys
    context = api.Context() if context is None else context
    plugins = api.discover() if plugins is None else plugins

    # Register targets
    for target in targets:
        api.register_target(target)

    # Do not consider inactive plug-ins
    plugins = list(p for p in plugins if p.active)
    collectors = list(p for p in plugins if lib.inrange(
        number=p.order,
        base=api.CollectorOrder)
    )

    # First pass, collection
    plugin_processed_count = 0
    for Plugin, instance in logic.Iterator(collectors, context):
        plugin_processed_count += 1
        percentage = float(plugin_processed_count) / len(plugins)
        yield (percentage, plugin.process(Plugin, context, instance), context)

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
    plugin_processing = None
    instances_processed_count = 0
    total_plugins = len(plugins) + len(collectors)
    for Plugin, instance in logic.Iterator(plugins, context, state):
        try:
            result = plugin.process(Plugin, context, instance)

            # Calculate percentage
            instances_count = len(logic.instances_by_plugin(context, Plugin))

            instances_processed_fraction = 0
            if instances_count != 0:
                instances_processed_fraction = (
                    float(instances_processed_count) / instances_count
                )

            plugin_instance_processed = (
                instances_processed_fraction + plugin_processed_count
            )
            percentage = plugin_instance_processed / total_plugins

            # Yield results
            yield (percentage, result, context)

            # Increment for next iteration
            instances_processed_count += 1
            if plugin_processing != Plugin:
                plugin_processed_count += 1
                instances_processed_count = 0
                plugin_processing = Plugin
        except StopIteration:  # End of items
            raise

        except Exception as e:  # This is unexpected, most likely a bug
            log.error("An exception occurred.\n")
            raise e

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

    # Deregister targets
    for target in targets:
        api.deregister_target(target)


def collect(context=None, plugins=None, targets=["default"]):
    """Convenience function for collection-only

     _________    . . . . .  .   . . . . . .   . . . . . . .
    |         |   .          .   .         .   .           .
    | Collect |-->. Validate .-->. Extract .-->. Integrate .
    |_________|   . . . . .  .   . . . . . .   . . . . . . .

    """

    context = _convenience(api.CollectorOrder, context, plugins, targets)
    api.emit("collected", context=context)
    return context


def validate(context=None, plugins=None, targets=["default"]):
    """Convenience function for validation-only

    . . . . . .    __________    . . . . . .   . . . . . . .
    .         .   |          |   .         .   .           .
    . Collect .-->| Validate |-->. Extract .-->. Integrate .
    . . . . . .   |__________|   . . . . . .   . . . . . . .

    """

    context = _convenience(api.ValidatorOrder, context, plugins, targets)
    api.emit("validated", context=context)
    return context


def extract(context=None, plugins=None, targets=["default"]):
    """Convenience function for extraction-only

    . . . . . .   . . . . .  .    _________    . . . . . . .
    .         .   .          .   |         |   .           .
    . Collect .-->. Validate .-->| Extract |-->. Integrate .
    . . . . . .   . . . . .  .   |_________|   . . . . . . .

    """

    context = _convenience(api.ExtractorOrder, context, plugins, targets)
    api.emit("extracted", context=context)
    return context


def integrate(context=None, plugins=None, targets=["default"]):
    """Convenience function for integration-only

    . . . . . .   . . . . .  .   . . . . . .    ___________
    .         .   .          .   .         .   |           |
    . Collect .-->. Validate .-->. Extract .-->| Integrate |
    . . . . . .   . . . . .  .   . . . . . .   |___________|

    """

    context = _convenience(api.IntegratorOrder, context, plugins, targets)
    api.emit("integrated", context=context)
    return context


def _convenience(order, context=None, plugins=None, targets=["default"]):
    plugins = list(
        p for p in (api.discover() if plugins is None else plugins)
        if lib.inrange(p.order, order)
    )

    return publish(context, plugins, targets)


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
