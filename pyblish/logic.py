"""Pyblish Logic

Dependencies are injected via third-party modules.

"""

import sys
import traceback

from plugin import Provider


class TestFailed(Exception):
    def __init__(self, msg, vars):
        super(TestFailed, self).__init__(msg)
        self.vars = vars


def test(**vars):
    """Evaluate whether or not to continue processing

    Variables:
        order (int): Current order
        errorOrders (list): Orders at which an error has occured

    """

    if vars["order"] >= 2:  # If validation is done
        for order in vars["errorOrders"]:
            if order < 2:  # Were there any error before validation?
                return False
    return True


def process(plugins, process, context):
    """Logical processor

    Takes callables and data as input, and performs
    logical operations on them.

    Raises:
        Exception when test fails.

    """

    def gen(plugin, instances):
        """Generate pair of context/instance"""
        if len(instances) > 0:
            for instance in instances:
                yield instance
        else:
            yield None

    vars = {
        "order": None,
        "errorOrders": list()
    }

    # Clear introspection values
    self = sys.modules[__name__]
    self.process.next_plugin = None
    self.process.next_instance = None

    for plugin in plugins:
        vars["order"] = plugin.order

        if test(**vars):
            instances = instances_by_plugin(context, plugin)

            # Process once, regardless of available instances if
            # plug-in isn't associated with any particular family.
            if not instances and "*" not in plugin.families:
                continue

            for instance in gen(plugin, instances):

                # Provide introspection
                self.process.next_instance = instance
                self.process.next_plugin = plugin

                try:
                    result = process(plugin, context, instance)

                except Exception as exception:
                    # If this happens, there is a bug
                    _extract_traceback(exception)
                    yield exception

                else:
                    # Make note of the order at which
                    # the potential error error occured.
                    if result["error"]:
                        if plugin.order not in vars["errorOrders"]:
                            vars["errorOrders"].append(plugin.order)
                    yield result

                # If the plug-in doesn't have a compatible instance,
                # and the context isn't being processed, discard plug-in.
                args = Provider.args(plugin.process)
                if "instance" not in args:
                    break

        else:
            yield TestFailed("Test failed", vars)


process.next_plugin = None
process.next_instance = None


def plugins_by_family(plugins, family):
    """Return compatible plugins `plugins` to family `family`

    Arguments:
        plugins (list): List of plugins
        family (str): Family with which to compare against

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
        if not hasattr(plugin, "families"):
            continue

        if any(x in plugin.families for x in (family, "*")):
            compatible.append(plugin)

    return compatible


def plugins_by_instance(plugins, instance):
    """Conveinence function for :func:`plugins_by_family`

    Arguments:
        plugins (list): Plug-ins to assess
        instance (Instance): Instance with which to compare against

    Returns:
        List of compatible plugins

    """

    return plugins_by_family(plugins, instance.data("family"))


def plugins_by_host(plugins, host):
    """Return compatible plugins `plugins` to host `host`

    Arguments:
        plugins (list): List of plugins
        host (str): Host with which compatible plugins are returned

    Returns:
        List of compatible plugins.

    """

    compatible = list()

    for plugin in plugins:
        if not hasattr(plugin, "hosts"):
            continue

        # TODO(marcus): Expand to take partial wildcards e.g. "*Mesh"
        if any(x in plugin.hosts for x in (host, "*")):
            compatible.append(plugin)

    return compatible


def instances_by_plugin(instances, plugin):
    """Return compatible instances `instances` to plugin `plugin`

    Arguments:
        instances (list): List of instances
        plugin (Plugin): Plugin with which to compare against

    Returns:
        List of compatible instances

    Invariant:
        Order of remaining plug-ins must remain the same

    """

    compatible = list()

    for instance in instances:
        if not hasattr(plugin, "families"):
            continue

        family = instance.data("family")
        if any(x in plugin.families for x in (family, "*")):
            compatible.append(instance)

    return compatible


def _extract_traceback(exception):
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)
