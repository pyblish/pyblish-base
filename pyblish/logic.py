"""Pyblish Logic

Dependencies are injected via third-party modules.

"""


TestFailed = type("TestFailed", (Exception,), {})


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

    def gen(plugin, context):
        """Generate pair of context/instance"""
        instances = instances_by_plugin(context, plugin)
        if len(instances) > 0:
            for instance in instances:
                yield context, instance
        else:
            yield context, None

    vars = {
        "order": None,
        "errorOrders": list()
    }

    results = list()

    for plugin in plugins:
        vars["order"] = plugin.order

        if test(**vars):
            for context, instance in gen(plugin, context):
                result = process(plugin, context, instance)
                if result["error"]:
                    vars["errorOrders"].append(plugin.order)

                results.append(result)
                yield result

        else:
            raise TestFailed("Test failed")


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
